#!/usr/bin/env python3
"""
登录页面测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bilibili_analyzer import create_app
from bilibili_analyzer.config import Config

def test_login_page():
    """测试登录页面"""
    app = create_app(Config)
    
    with app.test_client() as client:
        print("🧪 测试登录页面...")
        
        # 测试1: 访问登录页面
        print("📝 测试1: 访问登录页面")
        response = client.get('/login')
        if response.status_code == 200:
            print("✅ 登录页面访问成功")
        else:
            print(f"❌ 登录页面访问失败: {response.status_code}")
        
        # 测试2: 测试登录功能
        print("\n📝 测试2: 测试登录功能")
        response = client.post('/login', data={
            'username': 'admin',
            'password': 'admin',
            'remember': True
        })
        
        if response.status_code == 302:
            print("✅ 登录成功，重定向到仪表板")
            
            # 测试3: 访问仪表板
            print("\n📝 测试3: 访问仪表板")
            response = client.get('/dashboard')
            if response.status_code == 200:
                print("✅ 仪表板访问成功")
            else:
                print(f"❌ 仪表板访问失败: {response.status_code}")
        else:
            print(f"❌ 登录失败: {response.status_code}")
        
        # 测试4: 测试错误登录
        print("\n📝 测试4: 测试错误登录")
        response = client.post('/login', data={
            'username': 'wrong',
            'password': 'wrong'
        })
        
        if response.status_code == 200:
            print("✅ 错误登录处理正确")
        else:
            print(f"❌ 错误登录处理失败: {response.status_code}")
        
        # 测试5: 测试登出
        print("\n📝 测试5: 测试登出")
        response = client.get('/logout')
        if response.status_code == 302:
            print("✅ 登出成功")
        else:
            print(f"❌ 登出失败: {response.status_code}")

def test_dashboard_access():
    """测试仪表板访问权限"""
    app = create_app(Config)
    
    with app.test_client() as client:
        print("\n🧪 测试仪表板访问权限...")
        
        # 未登录访问仪表板
        response = client.get('/dashboard')
        if response.status_code == 302:
            print("✅ 未登录用户正确重定向到登录页面")
        else:
            print(f"❌ 未登录用户访问权限控制失败: {response.status_code}")

def test_api_endpoints():
    """测试API端点"""
    app = create_app(Config)
    
    with app.test_client() as client:
        print("\n🧪 测试API端点...")
        
        # 测试检查登录状态
        response = client.get('/api/check-auth')
        if response.status_code == 200:
            print("✅ 登录状态检查API正常")
        else:
            print(f"❌ 登录状态检查API失败: {response.status_code}")

if __name__ == '__main__':
    print("🚀 开始测试登录页面功能...")
    print("=" * 50)
    
    test_login_page()
    test_dashboard_access()
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
    
    # 提供测试账户信息
    print("\n📋 测试账户信息:")
    print("用户名: admin")
    print("密码: admin")
    print("用户名: user")
    print("密码: user")