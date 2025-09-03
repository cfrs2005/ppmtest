"""
大模型内容分析模块性能测试
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any
from datetime import datetime

from bilibili_analyzer.services import AnalysisService
from bilibili_analyzer.analyzers import ContentAnalyzer, AnalysisConfig
from bilibili_analyzer.cache import CacheManager, CacheConfig
from bilibili_analyzer.utils import TokenManager


class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.results = {}
    
    async def test_analysis_performance(self):
        """测试分析性能"""
        print("=== 分析性能测试 ===")
        
        # 准备测试数据
        test_cases = self._prepare_test_data()
        
        results = []
        
        for case_name, content in test_cases.items():
            print(f"\n测试案例: {case_name}")
            
            # 测试多次取平均值
            times = []
            token_counts = []
            
            for i in range(3):  # 每个案例测试3次
                start_time = time.time()
                
                try:
                    # 模拟分析（因为没有真实API）
                    result = await self._simulate_analysis(content)
                    
                    end_time = time.time()
                    analysis_time = end_time - start_time
                    
                    times.append(analysis_time)
                    token_counts.append(result.total_tokens)
                    
                    print(f"  第{i+1}次: {analysis_time:.2f}秒, {result.total_tokens} tokens")
                    
                except Exception as e:
                    print(f"  第{i+1}次失败: {e}")
                    continue
            
            if times:
                avg_time = statistics.mean(times)
                avg_tokens = statistics.mean(token_counts)
                
                results.append({
                    'case': case_name,
                    'avg_time': avg_time,
                    'min_time': min(times),
                    'max_time': max(times),
                    'avg_tokens': avg_tokens,
                    'content_length': len(content)
                })
                
                print(f"  平均时间: {avg_time:.2f}秒")
                print(f"  时间范围: {min(times):.2f} - {max(times):.2f}秒")
                print(f"  平均Token: {avg_tokens:.0f}")
        
        self.results['analysis_performance'] = results
        return results
    
    async def test_cache_performance(self):
        """测试缓存性能"""
        print("\n=== 缓存性能测试 ===")
        
        cache_manager = CacheManager(CacheConfig(
            max_size=1000,
            default_ttl=3600,
            enable_stats=True
        ))
        
        cache = cache_manager.get_memory_cache()
        
        # 测试数据
        test_data = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        
        # 测试写入性能
        print("测试写入性能...")
        write_times = []
        for key, value in test_data.items():
            start_time = time.time()
            cache.set(key, value)
            end_time = time.time()
            write_times.append(end_time - start_time)
        
        avg_write_time = statistics.mean(write_times)
        print(f"平均写入时间: {avg_write_time*1000:.2f}ms")
        
        # 测试读取性能
        print("测试读取性能...")
        read_times = []
        for key in test_data.keys():
            start_time = time.time()
            value = cache.get(key)
            end_time = time.time()
            read_times.append(end_time - start_time)
        
        avg_read_time = statistics.mean(read_times)
        print(f"平均读取时间: {avg_read_time*1000:.2f}ms")
        
        # 测试缓存命中率
        print("测试缓存命中率...")
        cache_hit_count = 0
        cache_miss_count = 0
        
        for i in range(200):
            key = f"key_{i % 150}"  # 部分命中，部分未命中
            value = cache.get(key)
            if value is not None:
                cache_hit_count += 1
            else:
                cache_miss_count += 1
        
        hit_rate = cache_hit_count / (cache_hit_count + cache_miss_count)
        print(f"缓存命中率: {hit_rate*100:.1f}%")
        
        cache_stats = cache.get_stats()
        print(f"缓存统计: {cache_stats}")
        
        results = {
            'avg_write_time_ms': avg_write_time * 1000,
            'avg_read_time_ms': avg_read_time * 1000,
            'hit_rate': hit_rate,
            'cache_stats': cache_stats
        }
        
        self.results['cache_performance'] = results
        return results
    
    async def test_chunking_performance(self):
        """测试分块性能"""
        print("\n=== 分块性能测试 ===")
        
        from bilibili_analyzer.analyzers.chunk_processor import ChunkProcessor, ChunkConfig
        
        # 测试不同大小的文本
        test_sizes = [1000, 5000, 10000, 20000, 50000]
        
        results = []
        
        for size in test_sizes:
            print(f"\n测试文本大小: {size} 字符")
            
            # 生成测试文本
            test_content = "这是一个测试句子。" * (size // 8)
            
            # 测试不同配置
            configs = [
                ChunkConfig(max_tokens=500, semantic_chunking=True),
                ChunkConfig(max_tokens=1000, semantic_chunking=True),
                ChunkConfig(max_tokens=2000, semantic_chunking=True),
                ChunkConfig(max_tokens=1000, semantic_chunking=False)
            ]
            
            for config in configs:
                processor = ChunkProcessor(config)
                
                # 测试分块性能
                times = []
                for i in range(5):
                    start_time = time.time()
                    chunks = processor.chunk_text(test_content)
                    end_time = time.time()
                    times.append(end_time - start_time)
                
                avg_time = statistics.mean(times)
                chunk_count = len(chunks)
                
                print(f"  配置: max_tokens={config.max_tokens}, semantic={config.semantic_chunking}")
                print(f"  平均时间: {avg_time*1000:.2f}ms")
                print(f"  分块数量: {chunk_count}")
                
                results.append({
                    'content_size': size,
                    'max_tokens': config.max_tokens,
                    'semantic_chunking': config.semantic_chunking,
                    'avg_time_ms': avg_time * 1000,
                    'chunk_count': chunk_count
                })
        
        self.results['chunking_performance'] = results
        return results
    
    async def test_concurrent_analysis(self):
        """测试并发分析性能"""
        print("\n=== 并发分析性能测试 ===")
        
        # 准备测试数据
        test_contents = []
        for i in range(10):
            content = f"这是第{i}个测试内容。" * 50
            test_contents.append(content)
        
        # 测试不同并发级别
        concurrency_levels = [1, 2, 5, 10]
        
        results = []
        
        for concurrency in concurrency_levels:
            print(f"\n测试并发级别: {concurrency}")
            
            # 分组测试
            groups = [test_contents[i:i+concurrency] for i in range(0, len(test_contents), concurrency)]
            
            total_times = []
            
            for group in groups:
                start_time = time.time()
                
                # 并发执行
                tasks = [self._simulate_analysis(content) for content in group]
                await asyncio.gather(*tasks)
                
                end_time = time.time()
                total_time = end_time - start_time
                total_times.append(total_time)
            
            avg_total_time = statistics.mean(total_times)
            avg_time_per_task = avg_total_time / concurrency
            
            print(f"  平均总时间: {avg_total_time:.2f}秒")
            print(f"  平均每个任务时间: {avg_time_per_task:.2f}秒")
            
            results.append({
                'concurrency': concurrency,
                'avg_total_time': avg_total_time,
                'avg_time_per_task': avg_time_per_task
            })
        
        self.results['concurrent_analysis'] = results
        return results
    
    async def test_memory_usage(self):
        """测试内存使用"""
        print("\n=== 内存使用测试 ===")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 测试不同操作对内存的影响
        tests = [
            ("初始状态", None),
            ("创建分析服务", lambda: AnalysisService()),
            ("创建缓存管理器", lambda: CacheManager(CacheConfig(max_size=10000))),
            ("创建Token管理器", lambda: TokenManager()),
            ("加载大量数据", lambda: self._load_large_dataset()),
        ]
        
        memory_usage = []
        
        for test_name, test_func in tests:
            if test_func:
                test_func()
            
            # 等待内存稳定
            time.sleep(0.5)
            
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            memory_usage.append({
                'test': test_name,
                'memory_mb': memory_mb
            })
            
            print(f"{test_name}: {memory_mb:.1f} MB")
        
        self.results['memory_usage'] = memory_usage
        return memory_usage
    
    async def test_cost_efficiency(self):
        """测试成本效率"""
        print("\n=== 成本效率测试 ===")
        
        token_manager = self.analysis_service.token_manager
        
        # 模拟不同场景的使用情况
        scenarios = [
            {
                'name': '轻度使用',
                'tokens': 1000,
                'cost': 0.01,
                'model': 'gpt-3.5-turbo',
                'task': 'summary'
            },
            {
                'name': '中度使用',
                'tokens': 5000,
                'cost': 0.05,
                'model': 'gpt-4',
                'task': 'analysis'
            },
            {
                'name': '重度使用',
                'tokens': 20000,
                'cost': 0.20,
                'model': 'gpt-4',
                'task': 'analysis'
            }
        ]
        
        results = []
        
        for scenario in scenarios:
            print(f"\n测试场景: {scenario['name']}")
            
            # 记录使用情况
            token_manager.record_usage(
                tokens=scenario['tokens'],
                cost=scenario['cost'],
                model=scenario['model'],
                task_type=scenario['task'],
                content="测试内容"
            )
            
            # 获取成本分析
            from bilibili_analyzer.utils import CostAnalyzer
            cost_analyzer = CostAnalyzer(token_manager)
            
            efficiency = cost_analyzer.analyze_cost_efficiency(scenario['task'])
            
            print(f"  Token使用: {scenario['tokens']}")
            print(f"  成本: ${scenario['cost']:.4f}")
            print(f"  效率分数: {efficiency.get('efficiency_score', 0):.1f}")
            
            results.append({
                'scenario': scenario['name'],
                'tokens': scenario['tokens'],
                'cost': scenario['cost'],
                'efficiency_score': efficiency.get('efficiency_score', 0)
            })
        
        self.results['cost_efficiency'] = results
        return results
    
    def _prepare_test_data(self) -> Dict[str, str]:
        """准备测试数据"""
        return {
            'short_text': "这是一个简短的测试文本。",
            'medium_text': """
            Python是一种高级编程语言，由Guido van Rossum于1991年创建。
            它具有简洁的语法和强大的功能，被广泛应用于Web开发、数据科学、人工智能等领域。
            Python的特点包括：易读易写、丰富的库支持、跨平台兼容性。
            学习Python相对简单，是初学者的理想选择。
            """,
            'long_text': """
            人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
            
            机器学习是人工智能的一个子领域，它使计算机能够从数据中学习和改进，而无需明确编程。
            深度学习是机器学习的一个子集，使用神经网络来模拟人脑的工作方式。
            
            自然语言处理（NLP）是人工智能的一个重要应用领域，专注于计算机与人类语言之间的交互。
            计算机视觉是另一个重要领域，使计算机能够理解和解释视觉信息。
            
            人工智能的应用包括：语音识别、图像识别、推荐系统、自动驾驶、医疗诊断等。
            随着技术的发展，AI正在改变我们的生活和工作方式。
            
            然而，AI也带来了一些挑战，包括隐私问题、就业影响、伦理考量等。
            负责任的AI开发需要考虑这些因素，确保技术的发展造福人类社会。
            
            未来，人工智能将继续发展，可能带来更多的创新和变革。
            我们需要平衡技术进步与社会责任，共同塑造AI的未来。
            """ * 3,
            'structured_data': json.dumps({
                "title": "Python编程教程",
                "chapters": [
                    {"title": "基础语法", "content": "变量、数据类型、控制结构"},
                    {"title": "函数", "content": "函数定义、参数、返回值"},
                    {"title": "面向对象", "content": "类、对象、继承、多态"},
                    {"title": "模块和包", "content": "导入、创建模块、包管理"}
                ]
            })
        }
    
    async def _simulate_analysis(self, content: str):
        """模拟分析过程"""
        # 模拟处理时间
        processing_time = len(content) * 0.0001  # 假设每字符处理0.1ms
        await asyncio.sleep(processing_time)
        
        # 模拟Token计算
        from bilibili_analyzer.analyzers.chunk_processor import SimpleTokenCounter
        token_counter = SimpleTokenCounter()
        tokens = token_counter.encode(content)
        
        # 模拟成本计算
        cost = tokens * 0.00001  # 假设每token成本$0.00001
        
        # 返回模拟结果
        from bilibili_analyzer.analyzers import AnalysisResult
        return AnalysisResult(
            summary=f"模拟总结，处理了{len(content)}字符",
            key_points=["关键点1", "关键点2"],
            categories=["测试", "模拟"],
            tags=["测试", "性能"],
            knowledge_entries=[],
            total_tokens=tokens,
            total_cost=cost,
            analysis_time=processing_time,
            model_used="gpt-3.5-turbo",
            chunk_count=1
        )
    
    def _load_large_dataset(self):
        """加载大数据集"""
        # 创建大量数据以测试内存使用
        large_data = []
        for i in range(1000):
            large_data.append({
                'id': i,
                'content': f"测试内容 {i}" * 100,
                'metadata': {'index': i, 'category': 'test'}
            })
        return large_data
    
    def generate_report(self):
        """生成性能测试报告"""
        print("\n" + "="*60)
        print("性能测试报告")
        print("="*60)
        
        # 分析性能
        if 'analysis_performance' in self.results:
            print("\n1. 分析性能测试结果:")
            for result in self.results['analysis_performance']:
                print(f"  {result['case']}: {result['avg_time']:.2f}秒平均, "
                      f"{result['avg_tokens']:.0f} tokens平均")
        
        # 缓存性能
        if 'cache_performance' in self.results:
            cache_perf = self.results['cache_performance']
            print(f"\n2. 缓存性能:")
            print(f"  平均写入时间: {cache_perf['avg_write_time_ms']:.2f}ms")
            print(f"  平均读取时间: {cache_perf['avg_read_time_ms']:.2f}ms")
            print(f"  缓存命中率: {cache_perf['hit_rate']*100:.1f}%")
        
        # 分块性能
        if 'chunking_performance' in self.results:
            print(f"\n3. 分块性能:")
            # 显示最佳配置
            best_semantic = min([r for r in self.results['chunking_performance'] if r['semantic_chunking']], 
                              key=lambda x: x['avg_time_ms'])
            best_simple = min([r for r in self.results['chunking_performance'] if not r['semantic_chunking']], 
                             key=lambda x: x['avg_time_ms'])
            
            print(f"  最佳语义分块: {best_semantic['avg_time_ms']:.2f}ms")
            print(f"  最佳简单分块: {best_simple['avg_time_ms']:.2f}ms")
        
        # 并发性能
        if 'concurrent_analysis' in self.results:
            print(f"\n4. 并发性能:")
            for result in self.results['concurrent_analysis']:
                print(f"  并发级别 {result['concurrency']}: "
                      f"{result['avg_time_per_task']:.2f}秒/任务")
        
        # 内存使用
        if 'memory_usage' in self.results:
            memory_usage = self.results['memory_usage']
            initial_memory = memory_usage[0]['memory_mb']
            final_memory = memory_usage[-1]['memory_mb']
            memory_increase = final_memory - initial_memory
            
            print(f"\n5. 内存使用:")
            print(f"  初始内存: {initial_memory:.1f} MB")
            print(f"  最终内存: {final_memory:.1f} MB")
            print(f"  内存增长: {memory_increase:.1f} MB")
        
        # 成本效率
        if 'cost_efficiency' in self.results:
            print(f"\n6. 成本效率:")
            for result in self.results['cost_efficiency']:
                print(f"  {result['scenario']}: "
                      f"${result['cost']:.4f}, 效率分数: {result['efficiency_score']:.1f}")
        
        print("\n" + "="*60)


async def main():
    """主函数"""
    print("大模型内容分析模块性能测试")
    print("=" * 50)
    
    test_suite = PerformanceTestSuite()
    
    try:
        # 运行所有性能测试
        await test_suite.test_analysis_performance()
        await test_suite.test_cache_performance()
        await test_suite.test_chunking_performance()
        await test_suite.test_concurrent_analysis()
        await test_suite.test_memory_usage()
        await test_suite.test_cost_efficiency()
        
        # 生成报告
        test_suite.generate_report()
        
    except Exception as e:
        print(f"性能测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())