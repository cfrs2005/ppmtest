"""
API性能测试脚本
"""

import time
import requests
import statistics
import concurrent.futures
from datetime import datetime

class APIPerformanceTester:
    """API性能测试器"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Bilibili-Analyzer-Performance-Test/1.0'
        })
    
    def test_endpoint_performance(self, method, endpoint, data=None, params=None, iterations=10):
        """测试单个端点的性能"""
        url = f"{self.base_url}{endpoint}"
        response_times = []
        success_count = 0
        error_count = 0
        
        print(f"\n🔬 测试 {method} {endpoint} ({iterations} 次请求)")
        
        for i in range(iterations):
            try:
                start_time = time.time()
                
                if method.upper() == 'GET':
                    response = self.session.get(url, params=params, timeout=10)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, timeout=10)
                else:
                    print(f"不支持的HTTP方法: {method}")
                    continue
                
                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response.status_code < 400:
                    success_count += 1
                else:
                    error_count += 1
                
                print(f"  请求 {i+1}: {response_time:.3f}s (状态码: {response.status_code})")
                
            except requests.exceptions.RequestException as e:
                error_count += 1
                print(f"  请求 {i+1}: 失败 - {e}")
        
        # 计算统计信息
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            print(f"  📊 性能统计:")
            print(f"    平均响应时间: {avg_time:.3f}s")
            print(f"    中位数响应时间: {median_time:.3f}s")
            print(f"    最小响应时间: {min_time:.3f}s")
            print(f"    最大响应时间: {max_time:.3f}s")
            print(f"    标准差: {std_dev:.3f}s")
            print(f"    成功率: {success_count/iterations*100:.1f}%")
            
            # 性能评级
            if avg_time < 0.1:
                grade = "🟢 优秀"
            elif avg_time < 0.5:
                grade = "🟡 良好"
            elif avg_time < 1.0:
                grade = "🟠 一般"
            else:
                grade = "🔴 较差"
            
            print(f"    性能评级: {grade}")
            
            return {
                'endpoint': endpoint,
                'method': method,
                'avg_time': avg_time,
                'median_time': median_time,
                'min_time': min_time,
                'max_time': max_time,
                'std_dev': std_dev,
                'success_rate': success_count/iterations,
                'total_requests': iterations,
                'success_count': success_count,
                'error_count': error_count
            }
        else:
            print(f"  ❌ 所有请求都失败了")
            return None
    
    def test_concurrent_performance(self, method, endpoint, data=None, params=None, concurrent_users=5, requests_per_user=10):
        """测试并发性能"""
        url = f"{self.base_url}{endpoint}"
        response_times = []
        success_count = 0
        error_count = 0
        
        print(f"\n🚀 并发测试 {method} {endpoint} ({concurrent_users} 用户, 每用户 {requests_per_user} 请求)")
        
        def make_requests():
            """发送请求的函数"""
            nonlocal response_times, success_count, error_count
            
            for i in range(requests_per_user):
                try:
                    start_time = time.time()
                    
                    if method.upper() == 'GET':
                        response = self.session.get(url, params=params, timeout=30)
                    elif method.upper() == 'POST':
                        response = self.session.post(url, json=data, timeout=30)
                    else:
                        continue
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    response_times.append(response_time)
                    
                    if response.status_code < 400:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    # 添加随机延迟，模拟真实用户行为
                    time.sleep(0.1 + (i % 3) * 0.1)
                    
                except requests.exceptions.RequestException as e:
                    error_count += 1
        
        # 使用线程池模拟并发用户
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_requests) for _ in range(concurrent_users)]
            concurrent.futures.wait(futures)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算统计信息
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            min_time = min(response_times)
            max_time = max(response_times)
            std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
            
            total_requests = concurrent_users * requests_per_user
            requests_per_second = total_requests / total_time if total_time > 0 else 0
            
            print(f"  📊 并发性能统计:")
            print(f"    总耗时: {total_time:.3f}s")
            print(f"    平均响应时间: {avg_time:.3f}s")
            print(f"    中位数响应时间: {median_time:.3f}s")
            print(f"    最小响应时间: {min_time:.3f}s")
            print(f"    最大响应时间: {max_time:.3f}s")
            print(f"    标准差: {std_dev:.3f}s")
            print(f"    成功率: {success_count/total_requests*100:.1f}%")
            print(f"    请求数/秒: {requests_per_second:.1f}")
            
            # 并发性能评级
            if requests_per_second > 50:
                grade = "🟢 优秀"
            elif requests_per_second > 20:
                grade = "🟡 良好"
            elif requests_per_second > 10:
                grade = "🟠 一般"
            else:
                grade = "🔴 较差"
            
            print(f"    并发性能评级: {grade}")
            
            return {
                'endpoint': endpoint,
                'method': method,
                'concurrent_users': concurrent_users,
                'requests_per_user': requests_per_user,
                'total_time': total_time,
                'avg_time': avg_time,
                'median_time': median_time,
                'min_time': min_time,
                'max_time': max_time,
                'std_dev': std_dev,
                'success_rate': success_count/total_requests,
                'requests_per_second': requests_per_second,
                'total_requests': total_requests,
                'success_count': success_count,
                'error_count': error_count
            }
        else:
            print(f"  ❌ 所有请求都失败了")
            return None
    
    def run_comprehensive_performance_test(self):
        """运行全面的性能测试"""
        print("🎯 开始全面的API性能测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().isoformat()}")
        print(f"测试目标: {self.base_url}")
        print("=" * 60)
        
        results = []
        
        # 基础端点性能测试
        basic_endpoints = [
            ('GET', '/api/v1/health'),
            ('GET', '/api/v1/ping'),
            ('GET', '/api/v1/info'),
            ('GET', '/api/v1/stats'),
        ]
        
        print("\n📋 基础端点性能测试")
        print("-" * 30)
        
        for method, endpoint in basic_endpoints:
            result = self.test_endpoint_performance(method, endpoint, iterations=20)
            if result:
                results.append(result)
        
        # 只读端点性能测试
        readonly_endpoints = [
            ('GET', '/api/v1/videos'),
            ('GET', '/api/v1/tags'),
            ('GET', '/api/v1/knowledge'),
            ('GET', '/api/v1/knowledge/search', None, {'q': 'test'}),
        ]
        
        print("\n📖 只读端点性能测试")
        print("-" * 30)
        
        for method, endpoint, *args in readonly_endpoints:
            params = args[0] if args else None
            result = self.test_endpoint_performance(method, endpoint, params=params, iterations=10)
            if result:
                results.append(result)
        
        # 并发性能测试
        print("\n🚀 并发性能测试")
        print("-" * 30)
        
        concurrent_endpoints = [
            ('GET', '/api/v1/health'),
            ('GET', '/api/v1/stats'),
        ]
        
        for method, endpoint in concurrent_endpoints:
            result = self.test_concurrent_performance(method, endpoint, concurrent_users=10, requests_per_user=5)
            if result:
                results.append(result)
        
        # 生成报告
        print("\n" + "=" * 60)
        print("📊 性能测试报告")
        print("=" * 60)
        
        # 按性能排序
        sorted_results = sorted(results, key=lambda x: x.get('avg_time', float('inf')))
        
        print("\n🏆 性能排行榜 (按平均响应时间)")
        print("-" * 50)
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"{i:2d}. {result['method']} {result['endpoint']}")
            print(f"    平均响应时间: {result['avg_time']:.3f}s")
            print(f"    成功率: {result['success_rate']*100:.1f}%")
            print()
        
        # 性能统计
        if results:
            avg_times = [r['avg_time'] for r in results if 'avg_time' in r]
            success_rates = [r['success_rate'] for r in results if 'success_rate' in r]
            
            print("📈 总体性能统计")
            print("-" * 30)
            print(f"测试端点数量: {len(results)}")
            print(f"平均响应时间: {statistics.mean(avg_times):.3f}s")
            print(f"平均成功率: {statistics.mean(success_rates)*100:.1f}%")
            print(f"最快响应时间: {min(avg_times):.3f}s")
            print(f"最慢响应时间: {max(avg_times):.3f}s")
            
            # 性能建议
            print("\n💡 性能优化建议")
            print("-" * 30)
            
            slow_endpoints = [r for r in results if r.get('avg_time', 0) > 0.5]
            if slow_endpoints:
                print("🐌 以下端点响应较慢，建议优化:")
                for result in slow_endpoints:
                    print(f"   - {result['method']} {result['endpoint']}: {result['avg_time']:.3f}s")
            
            low_success_endpoints = [r for r in results if r.get('success_rate', 0) < 0.95]
            if low_success_endpoints:
                print("⚠️  以下端点成功率较低，建议检查:")
                for result in low_success_endpoints:
                    print(f"   - {result['method']} {result['endpoint']}: {result['success_rate']*100:.1f}%")
            
            if not slow_endpoints and not low_success_endpoints:
                print("✅ 所有端点性能表现良好！")
        
        return results

def main():
    """主函数"""
    import sys
    
    # 获取基础URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    # 创建性能测试器
    tester = APIPerformanceTester(base_url)
    
    # 运行性能测试
    results = tester.run_comprehensive_performance_test()
    
    # 输出结果
    print(f"\n🎉 性能测试完成！")
    print(f"📄 详细结果已保存到: performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    # 保存结果到文件
    import json
    filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"📊 测试了 {len(results)} 个端点")
    
    # 检查是否所有端点都达到了性能要求
    all_good = True
    for result in results:
        if result.get('avg_time', 0) > 1.0 or result.get('success_rate', 0) < 0.9:
            all_good = False
            break
    
    if all_good:
        print("✅ 所有端点都达到了性能要求！")
        sys.exit(0)
    else:
        print("⚠️  部分端点未达到性能要求，请查看详细报告")
        sys.exit(1)

if __name__ == "__main__":
    main()