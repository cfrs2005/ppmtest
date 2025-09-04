"""
真实视频入库测试脚本
使用实际的B站视频进行完整测试
"""

import asyncio
import os
import sys
import json
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class RealVideoIngestionTester:
    """真实视频入库测试器"""
    
    def __init__(self):
        self.api_key = os.getenv("GLM_API_KEY")
        self.api_base = os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
        self.model = os.getenv("GLM_MODEL", "glm-4-flash")
        self.test_results = {}
        
        # 测试视频信息
        self.test_video = {
            "url": "https://www.bilibili.com/video/BV1HfaMzoED6",
            "bvid": "BV1HfaMzoED6"
        }
    
    def extract_bvid_from_url(self, url: str) -> Optional[str]:
        """从URL中提取BV号"""
        pattern = r'BV([a-zA-Z0-9]+)'
        match = re.search(pattern, url)
        return match.group(0) if match else None
    
    async def test_bilibili_api(self):
        """测试B站API调用"""
        print("=== B站API测试 ===")
        
        try:
            import requests
            
            # B站API端点
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={self.test_video['bvid']}"
            
            # 设置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": f"https://www.bilibili.com/video/{self.test_video['bvid']}"
            }
            
            print(f"🔄 调用B站API: {api_url}")
            
            # 发送请求
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("code") == 0:
                    video_info = data.get("data", {})
                    
                    print("✅ B站API调用成功")
                    print(f"   标题: {video_info.get('title', '未知')}")
                    print(f"   作者: {video_info.get('owner', {}).get('name', '未知')}")
                    print(f"   时长: {video_info.get('duration', 0)}秒")
                    print(f"   播放量: {video_info.get('stat', {}).get('view', 0):,}")
                    print(f"   发布时间: {datetime.fromtimestamp(video_info.get('pubdate', 0)).strftime('%Y-%m-%d')}")
                    
                    self.test_results["bilibili_api"] = {
                        "status": "success",
                        "video_info": video_info
                    }
                    
                    return video_info
                else:
                    print(f"❌ B站API返回错误: {data.get('message')}")
                    return None
            else:
                print(f"❌ B站API请求失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ B站API调用异常: {e}")
            return None
    
    async def test_subtitle_extraction(self, video_info: Dict[str, Any]):
        """测试字幕提取"""
        print("\n=== 字幕提取测试 ===")
        
        try:
            import requests
            
            # 获取字幕信息的API
            api_url = f"https://api.bilibili.com/x/player/v2?bvid={self.test_video['bvid']}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": f"https://www.bilibili.com/video/{self.test_video['bvid']}"
            }
            
            print(f"🔄 获取字幕信息...")
            
            response = requests.get(api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("code") == 0:
                    subtitle_info = data.get("data", {}).get("subtitle", {})
                    subtitles = subtitle_info.get("subtitles", [])
                    
                    if subtitles:
                        print(f"✅ 找到 {len(subtitles)} 个字幕")
                        
                        # 获取第一个字幕
                        first_subtitle = subtitles[0]
                        subtitle_url = first_subtitle.get("subtitle_url")
                        
                        if subtitle_url:
                            # 下载字幕内容
                            print(f"🔄 下载字幕内容...")
                            subtitle_response = requests.get(subtitle_url, timeout=10)
                            
                            if subtitle_response.status_code == 200:
                                # 字幕通常是JSON格式
                                subtitle_data = subtitle_response.json()
                                
                                # 提取字幕文本
                                subtitle_text = self._extract_subtitle_text(subtitle_data)
                                
                                print(f"✅ 字幕提取成功")
                                print(f"   字幕长度: {len(subtitle_text)}字符")
                                print(f"   语言: {first_subtitle.get('lan', '未知')}")
                                
                                self.test_results["subtitle_extraction"] = {
                                    "status": "success",
                                    "subtitle_text": subtitle_text[:500] + "..." if len(subtitle_text) > 500 else subtitle_text,
                                    "subtitle_info": first_subtitle
                                }
                                
                                return subtitle_text
                            else:
                                print(f"❌ 字幕下载失败: HTTP {subtitle_response.status_code}")
                        else:
                            print("❌ 字幕URL为空")
                    else:
                        print("❌ 该视频没有字幕")
                else:
                    print(f"❌ 字幕信息获取失败: {data.get('message')}")
            else:
                print(f"❌ 字幕API请求失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 字幕提取异常: {e}")
        
        return None
    
    def _extract_subtitle_text(self, subtitle_data: Dict[str, Any]) -> str:
        """从字幕数据中提取文本"""
        try:
            if "body" in subtitle_data:
                # JSON格式字幕
                text_parts = []
                for item in subtitle_data["body"]:
                    if "content" in item:
                        text_parts.append(item["content"])
                return " ".join(text_parts)
            else:
                # 其他格式，直接返回
                return str(subtitle_data)
        except Exception as e:
            logger.error(f"字幕文本提取失败: {e}")
            return ""
    
    async def test_content_analysis(self, subtitle_text: str):
        """测试内容分析"""
        print("\n=== 内容分析测试 ===")
        
        try:
            import openai
            
            # 创建客户端
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            
            # 如果字幕太长，进行截断
            max_length = 2000
            if len(subtitle_text) > max_length:
                subtitle_text = subtitle_text[:max_length] + "..."
            
            # 分析消息
            analysis_prompt = f"""
            请分析以下视频字幕内容，并提供：

            1. 内容总结（100-150字）
            2. 3-5个关键点
            3. 内容分类（2-3个）
            4. 相关标签（5-8个）
            5. 内容难度等级（初级/中级/高级）
            6. 情感倾向（积极/中性/消极）

            请以JSON格式返回结果。

            字幕内容：
            {subtitle_text}
            """
            
            print("🔄 使用GLM进行内容分析...")
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的视频内容分析助手，请提供准确、结构化的分析结果。"},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            analysis_result = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            print("✅ 内容分析成功")
            print(f"   Token使用: {tokens_used}")
            print(f"   分析结果长度: {len(analysis_result)}字符")
            
            # 尝试解析JSON
            try:
                parsed_result = json.loads(analysis_result)
                print(f"   总结: {parsed_result.get('内容总结', parsed_result.get('content_summary', 'N/A'))[:100]}...")
                key_points = parsed_result.get('关键点', parsed_result.get('key_points', []))
                print(f"   关键点数量: {len(key_points)}")
                categories = parsed_result.get('内容分类', parsed_result.get('categories', []))
                print(f"   分类: {', '.join(categories)}")
            except json.JSONDecodeError:
                print(f"   原始结果: {analysis_result[:200]}...")
            
            self.test_results["content_analysis"] = {
                "status": "success",
                "analysis_result": analysis_result,
                "tokens_used": tokens_used
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ 内容分析失败: {e}")
            return None
    
    async def test_knowledge_extraction(self, analysis_result: str):
        """测试知识提取"""
        print("\n=== 知识提取测试 ===")
        
        try:
            import openai
            
            client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            
            knowledge_prompt = f"""
            基于以下视频内容分析结果，提取结构化的知识条目。

            请提取3-5个最重要的知识点，每个知识点包含：
            - 标题（简洁明了）
            - 详细内容（50-100字）
            - 知识类型（概念/方法/应用/事实）
            - 重要性等级（1-5分）
            - 相关标签（2-4个）

            请以JSON数组格式返回。

            分析结果：
            {analysis_result}
            """
            
            print("🔄 提取结构化知识...")
            
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的知识提取助手，请提取有价值的知识点。"},
                    {"role": "user", "content": knowledge_prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            knowledge_result = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            print("✅ 知识提取成功")
            print(f"   Token使用: {tokens_used}")
            
            # 尝试解析JSON
            try:
                parsed_knowledge = json.loads(knowledge_result)
                print(f"   提取知识条目: {len(parsed_knowledge)}个")
                for i, knowledge in enumerate(parsed_knowledge, 1):
                    print(f"   {i}. {knowledge.get('标题', knowledge.get('title', 'N/A'))} (重要性: {knowledge.get('重要性等级', knowledge.get('importance', 'N/A'))}/5)")
            except json.JSONDecodeError:
                print(f"   原始结果: {knowledge_result[:200]}...")
            
            self.test_results["knowledge_extraction"] = {
                "status": "success",
                "knowledge_result": knowledge_result,
                "tokens_used": tokens_used
            }
            
            return knowledge_result
            
        except Exception as e:
            print(f"❌ 知识提取失败: {e}")
            return None
    
    async def run_complete_test(self):
        """运行完整的真实视频测试"""
        print("🚀 开始真实视频入库测试...")
        print(f"📹 测试视频: {self.test_video['url']}")
        print("=" * 60)
        
        # 1. 获取视频信息
        print("\n📋 步骤1: 获取视频信息")
        video_info = await self.test_bilibili_api()
        if not video_info:
            print("❌ 无法获取视频信息，测试终止")
            return False
        
        # 2. 提取字幕
        print("\n📋 步骤2: 提取字幕")
        subtitle_text = await self.test_subtitle_extraction(video_info)
        if not subtitle_text:
            print("⚠️  无法提取字幕，使用视频描述进行分析")
            subtitle_text = video_info.get("desc", "视频描述不可用")
        
        # 3. 内容分析
        print("\n📋 步骤3: 内容分析")
        analysis_result = await self.test_content_analysis(subtitle_text)
        if not analysis_result:
            print("❌ 内容分析失败")
            return False
        
        # 4. 知识提取
        print("\n📋 步骤4: 知识提取")
        knowledge_result = await self.test_knowledge_extraction(analysis_result)
        if not knowledge_result:
            print("❌ 知识提取失败")
            return False
        
        # 生成测试报告
        report = self.generate_test_report(video_info)
        
        print("\n" + "=" * 60)
        print("🎉 真实视频入库测试完成！")
        print("✅ 所有步骤执行成功")
        print("✅ GLM API集成正常")
        print("✅ 数据流程完整")
        
        return True
    
    def generate_test_report(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试报告"""
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "video_info": {
                "bvid": self.test_video["bvid"],
                "title": video_info.get("title"),
                "author": video_info.get("owner", {}).get("name"),
                "duration": video_info.get("duration"),
                "view_count": video_info.get("stat", {}).get("view"),
                "publish_date": datetime.fromtimestamp(video_info.get("pubdate", 0)).strftime('%Y-%m-%d')
            },
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results.values() if r["status"] == "success"),
                "success_rate": sum(1 for r in self.test_results.values() if r["status"] == "success") / len(self.test_results) * 100
            }
        }
        
        # 保存报告
        with open("real_video_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存到 real_video_test_report.json")
        return report


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
    tester = RealVideoIngestionTester()
    
    try:
        success = await tester.run_complete_test()
        
        if success:
            print("\n🎯 测试总结:")
            print("✅ 真实视频处理能力验证通过")
            print("✅ B站API集成正常")
            print("✅ GLM模型分析功能正常")
            print("✅ 完整的数据处理流程验证通过")
            print("\n🚀 系统已准备好处理实际视频内容！")
        else:
            print("\n⚠️  测试过程中遇到问题，请检查日志")
            
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())