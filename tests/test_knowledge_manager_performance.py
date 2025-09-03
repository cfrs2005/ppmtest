"""
知识库管理模块性能测试
"""

import time
import pytest
import random
import string
from datetime import datetime
from bilibili_analyzer.models import db, KnowledgeEntry, Analysis, Video, Subtitle, Tag
from bilibili_analyzer.managers import KnowledgeManager
from bilibili_analyzer.services.search import SearchService


class TestKnowledgeManagerPerformance:
    """知识库管理器性能测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.knowledge_manager = KnowledgeManager()
        self.search_service = SearchService()
    
    def setup_test_data(self, num_entries=100):
        """设置测试数据"""
        with pytest.raises(Exception):
            # 清理现有数据
            KnowledgeEntry.query.delete()
            Analysis.query.delete()
            Video.query.delete()
            Subtitle.query.delete()
            Tag.query.delete()
            db.session.commit()
        
        # 创建测试数据
        for i in range(num_entries):
            # 创建视频
            video = Video(
                bvid=f'test_bvid_{i}',
                title=f'测试视频 {i}',
                author=f'测试作者 {i}'
            )
            db.session.add(video)
            db.session.flush()
            
            # 创建字幕
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            # 创建分析记录
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary=f'测试总结 {i}',
                key_points=f'["关键点{i}-1", "关键点{i}-2"]',
                categories=f'["技术", "教育"]',
                tags=f'["Python", "编程", "标签{i}"]',
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            # 创建知识条目
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title=f'知识条目 {i}',
                content=f'这是第{i}个知识条目的详细内容，包含丰富的信息。',
                knowledge_type=random.choice(['concept', 'fact', 'method', 'tip']),
                importance=random.randint(1, 5)
            )
            db.session.add(knowledge_entry)
            
            # 添加标签
            for tag_name in [f'标签{i}', 'Python', '编程']:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                knowledge_entry.tags.append(tag)
            
            db.session.commit()
    
    def test_search_performance(self, app):
        """测试搜索性能"""
        with app.app_context():
            # 设置测试数据
            self.setup_test_data(50)
            
            # 测试不同查询的性能
            queries = [
                'Python',
                '编程',
                '知识条目',
                '测试',
                'concept',
                '重要'
            ]
            
            search_times = []
            for query in queries:
                start_time = time.time()
                results = self.knowledge_manager.search_knowledge(query)
                end_time = time.time()
                search_time = end_time - start_time
                search_times.append(search_time)
                
                print(f"查询 '{query}' 耗时: {search_time:.3f}秒, 返回 {len(results)} 条结果")
                
                # 验证性能要求
                assert search_time < 2.0, f"查询 '{query}' 耗时过长: {search_time:.3f}秒"
            
            # 计算平均搜索时间
            avg_search_time = sum(search_times) / len(search_times)
            print(f"平均搜索时间: {avg_search_time:.3f}秒")
            assert avg_search_time < 1.0, f"平均搜索时间过长: {avg_search_time:.3f}秒"
    
    def test_bulk_search_performance(self, app):
        """测试批量搜索性能"""
        with app.app_context():
            # 设置测试数据
            self.setup_test_data(100)
            
            # 批量搜索
            start_time = time.time()
            queries = [f'标签{i}' for i in range(20)]
            
            all_results = []
            for query in queries:
                results = self.knowledge_manager.search_knowledge(query)
                all_results.extend(results)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"批量搜索 {len(queries)} 个查询耗时: {total_time:.3f}秒")
            print(f"总共返回 {len(all_results)} 条结果")
            
            # 验证性能要求
            assert total_time < 10.0, f"批量搜索耗时过长: {total_time:.3f}秒"
    
    def test_export_performance(self, app):
        """测试导出性能"""
        with app.app_context():
            # 设置测试数据
            self.setup_test_data(100)
            
            # 测试不同格式的导出性能
            formats = ['json', 'markdown', 'csv']
            
            for format_type in formats:
                start_time = time.time()
                exported_data = self.knowledge_manager.export_knowledge(format_type)
                end_time = time.time()
                export_time = end_time - start_time
                
                print(f"导出 {format_type} 格式耗时: {export_time:.3f}秒, 数据大小: {len(exported_data)} 字符")
                
                # 验证性能要求
                assert export_time < 5.0, f"导出 {format_type} 格式耗时过长: {export_time:.3f}秒"
                assert len(exported_data) > 0
    
    def test_concurrent_search_performance(self, app):
        """测试并发搜索性能"""
        import threading
        
        with app.app_context():
            # 设置测试数据
            self.setup_test_data(50)
            
            # 定义搜索函数
            def search_worker(query, results_list):
                start_time = time.time()
                results = self.knowledge_manager.search_knowledge(query)
                end_time = time.time()
                results_list.append({
                    'query': query,
                    'time': end_time - start_time,
                    'results_count': len(results)
                })
            
            # 创建多个搜索线程
            queries = ['Python', '编程', '知识', '测试', 'concept']
            threads = []
            results = []
            
            for query in queries:
                thread = threading.Thread(target=search_worker, args=(query, results))
                threads.append(thread)
            
            # 启动所有线程
            start_time = time.time()
            for thread in threads:
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"并发搜索 {len(queries)} 个查询耗时: {total_time:.3f}秒")
            
            for result in results:
                print(f"查询 '{result['query']}' 耗时: {result['time']:.3f}秒, 返回 {result['results_count']} 条结果")
                assert result['time'] < 2.0, f"查询 '{result['query']}' 耗时过长: {result['time']:.3f}秒"
            
            assert total_time < 5.0, f"并发搜索总耗时过长: {total_time:.3f}秒"
    
    def test_memory_usage(self, app):
        """测试内存使用"""
        import psutil
        import os
        
        with app.app_context():
            # 获取初始内存使用
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 设置大量测试数据
            self.setup_test_data(200)
            
            # 执行搜索操作
            for i in range(10):
                query = f'标签{i}'
                results = self.knowledge_manager.search_knowledge(query)
            
            # 执行导出操作
            exported_data = self.knowledge_manager.export_knowledge('json')
            
            # 获取最终内存使用
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"初始内存使用: {initial_memory:.2f} MB")
            print(f"最终内存使用: {final_memory:.2f} MB")
            print(f"内存增加: {memory_increase:.2f} MB")
            
            # 验证内存使用是否合理
            assert memory_increase < 100, f"内存使用增加过多: {memory_increase:.2f} MB"
    
    def test_database_query_performance(self, app):
        """测试数据库查询性能"""
        with app.app_context():
            # 设置测试数据
            self.setup_test_data(100)
            
            # 测试各种查询性能
            queries = [
                # 基本查询
                lambda: KnowledgeEntry.query.all(),
                
                # 带条件的查询
                lambda: KnowledgeEntry.query.filter(KnowledgeEntry.knowledge_type == 'concept').all(),
                
                # 带排序的查询
                lambda: KnowledgeEntry.query.order_by(KnowledgeEntry.created_at.desc()).all(),
                
                # 带分页的查询
                lambda: KnowledgeEntry.query.offset(10).limit(20).all(),
                
                # 关联查询
                lambda: KnowledgeEntry.query.join(KnowledgeEntry.tags).filter(Tag.name == 'Python').all(),
                
                # 统计查询
                lambda: db.session.query(KnowledgeEntry.knowledge_type, db.func.count(KnowledgeEntry.id)).group_by(KnowledgeEntry.knowledge_type).all()
            ]
            
            query_names = [
                '基本查询',
                '条件查询',
                '排序查询',
                '分页查询',
                '关联查询',
                '统计查询'
            ]
            
            for query_func, name in zip(queries, query_names):
                start_time = time.time()
                result = query_func()
                end_time = time.time()
                query_time = end_time - start_time
                
                print(f"{name} 耗时: {query_time:.3f}秒, 返回 {len(result) if hasattr(result, '__len__') else 'N/A'} 条结果")
                
                # 验证查询性能
                assert query_time < 1.0, f"{name} 耗时过长: {query_time:.3f}秒"
    
    def test_index_performance(self, app):
        """测试索引性能"""
        with app.app_context():
            # 设置测试数据
            self.setup_test_data(100)
            
            # 测试带索引的查询性能
            start_time = time.time()
            results = self.knowledge_manager.search_knowledge('Python')
            end_time = time.time()
            indexed_time = end_time - start_time
            
            print(f"索引查询耗时: {indexed_time:.3f}秒, 返回 {len(results)} 条结果")
            
            # 验证索引性能
            assert indexed_time < 0.5, f"索引查询耗时过长: {indexed_time:.3f}秒"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])