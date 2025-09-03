"""
API验证脚本 - 快速验证API是否正常工作
"""

import requests
import json
import time
from datetime import datetime

class APIValidator:
    """API验证器"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Bilibili-Analyzer-API-Validator/1.0'
        })
    
    def validate_endpoint(self, method, endpoint, expected_status=200, data=None, params=None):
        """验证单个端点"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=5)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=5)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=5)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=5)
            else:
                return False, f"不支持的HTTP方法: {method}"
            
            response_time = time.time() - start_time
            
            if response.status_code == expected_status:
                return True, {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': True
                }
            else:
                return False, {
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': False,
                    'error': f"期望状态码 {expected_status}，实际得到 {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            return False, {
                'success': False,
                'error': f"请求失败: {str(e)}"
            }
    
    def validate_basic_functionality(self):
        """验证基础功能"""
        print("🔍 验证基础功能")
        print("-" * 30)
        
        tests = [
            ('GET', '/api/v1/health', 200),
            ('GET', '/api/v1/ping', 200),
            ('GET', '/api/v1/info', 200),
            ('GET', '/api/v1/stats', 200),
        ]
        
        passed = 0
        failed = 0
        
        for method, endpoint, expected_status in tests:
            success, result = self.validate_endpoint(method, endpoint, expected_status)
            
            if success:
                print(f"✅ {method} {endpoint} - {result['response_time']:.3f}s")
                passed += 1
            else:
                print(f"❌ {method} {endpoint} - {result.get('error', 'Unknown error')}")
                failed += 1
        
        print(f"\n基础功能验证结果: {passed} 通过, {failed} 失败")
        return failed == 0
    
    def validate_error_handling(self):
        """验证错误处理"""
        print("\n🚨 验证错误处理")
        print("-" * 30)
        
        tests = [
            ('GET', '/api/v1/video/nonexistent', 404),  # 视频不存在
            ('GET', '/api/v1/knowledge/999999', 404),  # 知识条目不存在
            ('POST', '/api/v1/video/extract', 400, {}),  # 缺少bvid
            ('POST', '/api/v1/knowledge', 400, {}),  # 缺少title和content
        ]
        
        passed = 0
        failed = 0
        
        for method, endpoint, expected_status, *args in tests:
            data = args[0] if args else None
            success, result = self.validate_endpoint(method, endpoint, expected_status, data=data)
            
            if success:
                print(f"✅ {method} {endpoint} - 正确返回 {expected_status}")
                passed += 1
            else:
                print(f"❌ {method} {endpoint} - {result.get('error', 'Unknown error')}")
                failed += 1
        
        print(f"\n错误处理验证结果: {passed} 通过, {failed} 失败")
        return failed == 0
    
    def validate_response_format(self):
        """验证响应格式"""
        print("\n📋 验证响应格式")
        print("-" * 30)
        
        # 测试健康检查响应格式
        success, result = self.validate_endpoint('GET', '/api/v1/health')
        
        if success:
            try:
                response = self.session.get(f"{self.base_url}/api/v1/health")
                data = response.json()
                
                required_fields = ['success', 'message', 'timestamp', 'data']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"❌ 健康检查响应缺少字段: {missing_fields}")
                    return False
                else:
                    print("✅ 健康检查响应格式正确")
                    return True
            except (json.JSONDecodeError, requests.exceptions.RequestException) as e:
                print(f"❌ 健康检查响应格式错误: {e}")
                return False
        else:
            print(f"❌ 健康检查端点不可用: {result.get('error', 'Unknown error')}")
            return False
    
    def validate_performance_requirements(self):
        """验证性能要求"""
        print("\n⚡ 验证性能要求")
        print("-" * 30)
        
        # 测试快速响应的端点
        fast_endpoints = [
            ('GET', '/api/v1/health'),
            ('GET', '/api/v1/ping'),
        ]
        
        all_passed = True
        
        for method, endpoint in fast_endpoints:
            success, result = self.validate_endpoint(method, endpoint)
            
            if success:
                response_time = result['response_time']
                if response_time < 0.1:
                    print(f"✅ {method} {endpoint} - {response_time:.3f}s (优秀)")
                elif response_time < 0.5:
                    print(f"✅ {method} {endpoint} - {response_time:.3f}s (良好)")
                else:
                    print(f"⚠️  {method} {endpoint} - {response_time:.3f}s (较慢)")
                    all_passed = False
            else:
                print(f"❌ {method} {endpoint} - {result.get('error', 'Unknown error')}")
                all_passed = False
        
        print(f"\n性能要求验证结果: {'通过' if all_passed else '失败'}")
        return all_passed
    
    def validate_api_documentation(self):
        """验证API文档"""
        print("\n📚 验证API文档")
        print("-" * 30)
        
        # 测试文档页面
        success, result = self.validate_endpoint('GET', '/api/docs')
        
        if success:
            print("✅ API文档页面可访问")
            
            # 测试OpenAPI规范
            success, result = self.validate_endpoint('GET', '/api/docs/openapi.json')
            if success:
                print("✅ OpenAPI规范可访问")
                return True
            else:
                print(f"❌ OpenAPI规范不可访问: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API文档页面不可访问: {result.get('error', 'Unknown error')}")
            return False
    
    def run_comprehensive_validation(self):
        """运行全面验证"""
        print("🎯 开始API全面验证")
        print("=" * 60)
        print(f"验证时间: {datetime.now().isoformat()}")
        print(f"验证目标: {self.base_url}")
        print("=" * 60)
        
        # 运行所有验证
        results = {
            'basic_functionality': self.validate_basic_functionality(),
            'error_handling': self.validate_error_handling(),
            'response_format': self.validate_response_format(),
            'performance': self.validate_performance_requirements(),
            'documentation': self.validate_api_documentation()
        }
        
        # 输出结果
        print("\n" + "=" * 60)
        print("🏆 验证结果总结")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:20}: {status}")
        
        all_passed = all(results.values())
        print(f"\n🎯 总体结果: {'✅ 所有验证通过' if all_passed else '❌ 存在验证失败'}")
        
        if all_passed:
            print("\n🎉 API验证完成！系统可以正常使用。")
            print("\n📖 查看API文档: http://localhost:5000/api/docs")
            print("🚀 开始使用API进行开发吧！")
        else:
            print("\n⚠️  API验证发现问题，请检查系统配置。")
        
        return all_passed

def main():
    """主函数"""
    import sys
    
    # 获取基础URL
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    # 创建验证器
    validator = APIValidator(base_url)
    
    # 运行验证
    success = validator.run_comprehensive_validation()
    
    # 退出代码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()