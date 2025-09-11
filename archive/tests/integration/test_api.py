"""
API集成测试脚本
"""

import json
import requests
import time
from datetime import datetime

class APITester:
    """API测试类"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Bilibili-Analyzer-API-Test/1.0'
        })
    
    def test_endpoint(self, method, endpoint, data=None, params=None):
        """测试单个端点"""
        url = f"{self.base_url}{endpoint}"
        
        print(f"\n--- 测试 {method} {url} ---")
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                print(f"不支持的HTTP方法: {method}")
                return False
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.headers.get('content-type', '').startswith('application/json'):
                response_data = response.json()
                print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            else:
                print(f"响应内容: {response.text[:500]}...")
            
            # 检查响应时间
            response_time = response.elapsed.total_seconds()
            print(f"响应时间: {response_time:.3f}秒")
            
            # 检查性能
            if response_time > 1.0:
                print(f"⚠️  响应时间过长: {response_time:.3f}秒")
            elif response_time > 0.5:
                print(f"⚠️  响应时间较慢: {response_time:.3f}秒")
            else:
                print(f"✅ 响应时间良好: {response_time:.3f}秒")
            
            return response.status_code < 400
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return False
    
    def run_basic_tests(self):
        """运行基础测试"""
        print("🚀 开始API基础测试")
        print(f"测试时间: {datetime.now().isoformat()}")
        print(f"测试目标: {self.base_url}")
        
        tests = [
            # 健康检查
            ('GET', '/api/v1/health'),
            ('GET', '/api/v1/ping'),
            ('GET', '/api/v1/info'),
            
            # 统计接口
            ('GET', '/api/v1/stats'),
            ('GET', '/api/v1/stats/analysis'),
            ('GET', '/api/v1/stats/knowledge'),
            ('GET', '/api/v1/stats/performance'),
            ('GET', '/api/v1/health/detailed'),
            
            # 标签接口
            ('GET', '/api/v1/tags'),
            ('GET', '/api/v1/tags/popular'),
        ]
        
        passed = 0
        failed = 0
        
        for method, endpoint in tests:
            if self.test_endpoint(method, endpoint):
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 测试结果:")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📈 成功率: {passed/(passed+failed)*100:.1f}%")
        
        return failed == 0
    
    def test_video_workflow(self):
        """测试视频处理工作流"""
        print("\n🎬 测试视频处理工作流")
        
        # 这里使用一个示例BV号（实际使用时需要替换为真实有效的BV号）
        test_bvid = "BV1GJ411x7h7"  # 示例BV号
        
        workflow_tests = [
            # 1. 提取视频信息
            ('POST', '/api/v1/video/extract', {'bvid': test_bvid}),
            
            # 2. 获取视频信息
            ('GET', f'/api/v1/video/{test_bvid}'),
            
            # 3. 获取视频列表
            ('GET', '/api/v1/videos'),
        ]
        
        passed = 0
        failed = 0
        
        for method, endpoint, *args in workflow_tests:
            data = args[0] if args else None
            if self.test_endpoint(method, endpoint, data=data):
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 视频工作流测试结果:")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        
        return failed == 0
    
    def test_knowledge_workflow(self):
        """测试知识库工作流"""
        print("\n📚 测试知识库工作流")
        
        workflow_tests = [
            # 1. 搜索知识库
            ('GET', '/api/v1/knowledge/search', params={'q': 'test'}),
            
            # 2. 获取知识条目列表
            ('GET', '/api/v1/knowledge'),
            
            # 3. 获取知识库统计
            ('GET', '/api/v1/knowledge/stats'),
        ]
        
        passed = 0
        failed = 0
        
        for method, endpoint, *args in workflow_tests:
            params = args[0] if args else None
            if self.test_endpoint(method, endpoint, params=params):
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 知识库工作流测试结果:")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        
        return failed == 0
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🚨 测试错误处理")
        
        error_tests = [
            # 404错误
            ('GET', '/api/v1/video/nonexistent'),
            ('GET', '/api/v1/knowledge/999999'),
            ('GET', '/api/v1/analysis/999999'),
            
            # 400错误
            ('POST', '/api/v1/video/extract', {}),  # 缺少bvid
            ('POST', '/api/v1/knowledge', {}),  # 缺少title和content
            
            # 405错误
            ('POST', '/api/v1/stats'),  # 不支持的POST方法
        ]
        
        passed = 0
        failed = 0
        
        for method, endpoint, *args in error_tests:
            data = args[0] if args else None
            if self.test_endpoint(method, endpoint, data=data):
                # 对于错误测试，我们期望收到错误响应
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 错误处理测试结果:")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        
        return failed == 0
    
    def test_performance(self):
        """测试性能"""
        print("\n⚡ 测试性能")
        
        # 测试快速响应的端点
        fast_endpoints = [
            ('GET', '/api/v1/health'),
            ('GET', '/api/v1/ping'),
            ('GET', '/api/v1/stats'),
        ]
        
        total_time = 0
        passed = 0
        failed = 0
        
        for method, endpoint in fast_endpoints:
            start_time = time.time()
            if self.test_endpoint(method, endpoint):
                end_time = time.time()
                response_time = end_time - start_time
                total_time += response_time
                
                if response_time < 0.1:
                    print(f"✅ {endpoint}: {response_time:.3f}秒")
                    passed += 1
                else:
                    print(f"⚠️  {endpoint}: {response_time:.3f}秒 (超过0.1秒)")
                    failed += 1
            else:
                failed += 1
        
        avg_time = total_time / passed if passed > 0 else 0
        print(f"\n📊 性能测试结果:")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"⏱️  平均响应时间: {avg_time:.3f}秒")
        
        return failed == 0
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始完整的API测试")
        print("=" * 60)
        
        start_time = time.time()
        
        results = {
            'basic': self.run_basic_tests(),
            'video': self.test_video_workflow(),
            'knowledge': self.test_knowledge_workflow(),
            'error_handling': self.test_error_handling(),
            'performance': self.test_performance()
        }
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 60)
        print("🏆 测试总结")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:15}: {status}")
        
        all_passed = all(results.values())
        print(f"\n🎯 总体结果: {'✅ 所有测试通过' if all_passed else '❌ 存在失败测试'}")
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        
        return all_passed

def main():
    """主函数"""
    import sys
    
    # 获取基础URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    # 创建测试器
    tester = APITester(base_url)
    
    # 运行测试
    success = tester.run_all_tests()
    
    # 退出代码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()