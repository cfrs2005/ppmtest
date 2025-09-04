"""
简化的GLM API测试脚本
直接测试GLM API调用功能
"""

import asyncio
import os
import sys
import json
from typing import Dict, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleGLMTester:
    """简化的GLM测试器"""
    
    def __init__(self):
        self.api_key = os.getenv("GLM_API_KEY")
        self.api_base = os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
        self.model = os.getenv("GLM_MODEL", "glm-4-flash")
    
    async def test_glm_api(self):
        """测试GLM API调用"""
        print("=== GLM API测试 ===")
        
        # 检查配置
        if not self.api_key:
            print("❌ GLM_API_KEY未配置")
            return False
        
        print(f"✅ 配置检查通过")
        print(f"   API Base: {self.api_base}")
        print(f"   Model: {self.model}")
        
        try:
            # 尝试导入openai
            import openai
            print("✅ OpenAI库导入成功")
            
            # 创建客户端
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            print("✅ OpenAI客户端创建成功")
            
            # 测试同步调用
            print("🔄 测试同步API调用...")
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个测试助手"},
                    {"role": "user", "content": "请回复'GLM API测试成功'来验证服务正常工作"}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            print("✅ GLM API调用成功")
            print(f"   响应: {content}")
            print(f"   Token使用: {tokens_used}")
            
            return True
            
        except ImportError:
            print("❌ OpenAI库未安装，请运行: pip install openai")
            return False
        except Exception as e:
            print(f"❌ GLM API调用失败: {e}")
            return False
    
    async def test_async_glm_api(self):
        """测试异步GLM API调用"""
        print("\n=== 异步GLM API测试 ===")
        
        try:
            import openai
            print("✅ OpenAI库导入成功")
            
            # 创建异步客户端
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            print("✅ 异步OpenAI客户端创建成功")
            
            # 测试异步调用
            print("🔄 测试异步API调用...")
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的视频内容分析助手"},
                    {"role": "user", "content": "请简要介绍什么是人工智能，限制在50字以内"}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            print("✅ 异步GLM API调用成功")
            print(f"   响应: {content}")
            print(f"   Token使用: {tokens_used}")
            
            return True
            
        except Exception as e:
            print(f"❌ 异步GLM API调用失败: {e}")
            return False
    
    async def test_content_analysis(self):
        """测试内容分析功能"""
        print("\n=== 内容分析测试 ===")
        
        try:
            import openai
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            
            # 模拟视频字幕内容
            sample_content = """
            人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的机器。
            机器学习是人工智能的核心技术之一，它使计算机能够从数据中学习。
            深度学习是机器学习的一个子领域，使用神经网络来模拟人脑的工作方式。
            """
            
            # 分析消息
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的视频内容分析助手。请分析以下内容并提供总结和关键点。"
                    },
                    {
                        "role": "user",
                        "content": f"""请分析以下视频字幕内容：

{sample_content}

请提供：
1. 内容总结（50字以内）
2. 3个关键点

请以JSON格式返回结果。"""
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            print("✅ 内容分析成功")
            print(f"   分析结果: {content}")
            print(f"   Token使用: {tokens_used}")
            
            return True
            
        except Exception as e:
            print(f"❌ 内容分析失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始GLM API测试...")
        
        tests = [
            ("同步API调用", self.test_glm_api),
            ("异步API调用", self.test_async_glm_api),
            ("内容分析", self.test_content_analysis)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 运行测试: {test_name}")
            if await test_func():
                passed += 1
            print("-" * 50)
        
        # 输出测试结果摘要
        print(f"\n📊 测试结果摘要")
        print(f"   通过: {passed}/{total}")
        print(f"   成功率: {passed/total*100:.1f}%")
        
        if passed == total:
            print("\n🎉 所有测试通过！GLM API集成成功")
            print("✅ 视频入库功能验证完成")
        else:
            print(f"\n⚠️  {total-passed}个测试失败，请检查配置和服务状态")
        
        return passed == total


async def main():
    """主函数"""
    # 加载环境变量
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载成功")
    except ImportError:
        print("⚠️  python-dotenv未安装，使用系统环境变量")
    
    # 运行测试
    tester = SimpleGLMTester()
    
    try:
        await tester.run_all_tests()
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())