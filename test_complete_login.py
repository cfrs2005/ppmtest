#!/usr/bin/env python3
"""
完整的登录系统测试脚本
"""

import requests
import time

def test_login_system():
    """测试完整的登录系统"""
    base_url = "http://localhost:5000"
    
    print("🧪 测试登录系统...")
    print("=" * 50)
    
    # 测试1: 访问首页，应该重定向到登录页面
    print("📝 测试1: 访问首页重定向")
    try:
        response = requests.get(base_url)
        if response.url.endswith('/login'):
            print("✅ 首页正确重定向到登录页面")
        else:
            print(f"❌ 首页重定向失败: {response.url}")
    except Exception as e:
        print(f"❌ 首页访问失败: {e}")
    
    # 测试2: 访问登录页面
    print("\n📝 测试2: 访问登录页面")
    try:
        response = requests.get(f"{base_url}/login")
        if response.status_code == 200:
            print("✅ 登录页面访问成功")
            if "Bilibili视频分析系统" in response.text:
                print("✅ 页面内容正确")
            else:
                print("❌ 页面内容不正确")
        else:
            print(f"❌ 登录页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 登录页面访问失败: {e}")
    
    # 测试3: 错误登录
    print("\n📝 测试3: 错误登录")
    try:
        response = requests.post(f"{base_url}/login", data={
            'username': 'wrong',
            'password': 'wrong'
        })
        if response.status_code == 200:
            print("✅ 错误登录处理正确")
            if "用户名或密码错误" in response.text:
                print("✅ 错误信息显示正确")
            else:
                print("❌ 错误信息显示不正确")
        else:
            print(f"❌ 错误登录处理失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 错误登录测试失败: {e}")
    
    # 测试4: 正确登录
    print("\n📝 测试4: 正确登录")
    try:
        response = requests.post(f"{base_url}/login", data={
            'username': 'admin',
            'password': 'admin'
        }, allow_redirects=False)
        
        if response.status_code == 302:
            print("✅ 登录成功，返回重定向")
            
            # 获取重定向URL
            redirect_url = response.headers.get('Location', '')
            if redirect_url.endswith('/dashboard'):
                print("✅ 重定向到仪表板")
                
                # 测试5: 访问仪表板
                print("\n📝 测试5: 访问仪表板")
                response = requests.get(f"{base_url}/dashboard")
                if response.status_code == 200:
                    print("✅ 仪表板访问成功")
                    if "欢迎回来" in response.text:
                        print("✅ 仪表板内容正确")
                    else:
                        print("❌ 仪表板内容不正确")
                else:
                    print(f"❌ 仪表板访问失败: {response.status_code}")
            else:
                print(f"❌ 重定向URL不正确: {redirect_url}")
        else:
            print(f"❌ 登录失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 登录测试失败: {e}")
    
    # 测试6: 登出
    print("\n📝 测试6: 登出")
    try:
        response = requests.get(f"{base_url}/logout", allow_redirects=False)
        if response.status_code == 302:
            print("✅ 登出成功")
            
            # 验证登出后无法访问仪表板
            response = requests.get(f"{base_url}/dashboard")
            if response.status_code == 302:
                print("✅ 登出后无法访问仪表板")
            else:
                print("❌ 登出后仍能访问仪表板")
        else:
            print(f"❌ 登出失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 登出测试失败: {e}")
    
    # 测试7: API检查登录状态
    print("\n📝 测试7: API检查登录状态")
    try:
        response = requests.get(f"{base_url}/api/check-auth")
        if response.status_code == 200:
            data = response.json()
            if not data.get('logged_in', False):
                print("✅ 未登录状态检查正确")
            else:
                print("❌ 未登录状态检查错误")
        else:
            print(f"❌ API调用失败: {response.status_code}")
    except Exception as e:
        print(f"❌ API测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    
    print("\n📋 系统信息:")
    print("🔗 服务地址: http://localhost:5000")
    print("🔐 登录页面: http://localhost:5000/login")
    print("📊 仪表板: http://localhost:5000/dashboard")
    print("\n👤 测试账户:")
    print("用户名: admin")
    print("密码: admin")
    print("\n用户名: user")
    print("密码: user")

if __name__ == '__main__':
    print("🚀 开始测试登录系统...")
    test_login_system()