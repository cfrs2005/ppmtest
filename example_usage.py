"""
API使用示例脚本
"""

import requests
import json
import time
from datetime import datetime

class BilibiliAnalyzerClient:
    """Bilibili分析器API客户端"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Bilibili-Analyzer-Client/1.0'
        })
    
    def check_health(self):
        """检查服务健康状态"""
        response = self.session.get(f"{self.base_url}/api/v1/health")
        return response.json()
    
    def get_system_info(self):
        """获取系统信息"""
        response = self.session.get(f"{self.base_url}/api/v1/info")
        return response.json()
    
    def get_system_stats(self):
        """获取系统统计"""
        response = self.session.get(f"{self.base_url}/api/v1/stats")
        return response.json()
    
    def extract_video_info(self, bvid):
        """提取视频信息"""
        data = {'bvid': bvid}
        response = self.session.post(f"{self.base_url}/api/v1/video/extract", json=data)
        return response.json()
    
    def download_subtitle(self, bvid, language='zh-CN'):
        """下载字幕"""
        data = {'bvid': bvid, 'language': language}
        response = self.session.post(f"{self.base_url}/api/v1/subtitle/download", json=data)
        return response.json()
    
    def analyze_content(self, bvid, language='zh-CN', force_reanalyze=False):
        """分析内容"""
        data = {
            'bvid': bvid,
            'language': language,
            'force_reanalyze': force_reanalyze
        }
        response = self.session.post(f"{self.base_url}/api/v1/analyze", json=data)
        return response.json()
    
    def search_knowledge(self, query, limit=50):
        """搜索知识库"""
        params = {'q': query, 'limit': limit}
        response = self.session.get(f"{self.base_url}/api/v1/knowledge/search", params=params)
        return response.json()
    
    def create_knowledge_entry(self, title, content, knowledge_type='concept', importance=3, tags=None):
        """创建知识条目"""
        data = {
            'title': title,
            'content': content,
            'knowledge_type': knowledge_type,
            'importance': importance,
            'tags': tags or []
        }
        response = self.session.post(f"{self.base_url}/api/v1/knowledge", json=data)
        return response.json()
    
    def get_knowledge_entries(self, page=1, per_page=20):
        """获取知识条目列表"""
        params = {'page': page, 'per_page': per_page}
        response = self.session.get(f"{self.base_url}/api/v1/knowledge", params=params)
        return response.json()
    
    def get_tags(self, page=1, per_page=20):
        """获取标签列表"""
        params = {'page': page, 'per_page': per_page}
        response = self.session.get(f"{self.base_url}/api/v1/tags", params=params)
        return response.json()
    
    def create_tag(self, name, color='#007bff'):
        """创建标签"""
        data = {'name': name, 'color': color}
        response = self.session.post(f"{self.base_url}/api/v1/tags", json=data)
        return response.json()

def demo_basic_usage():
    """演示基本使用"""
    print("🎬 Bilibili视频分析系统API使用示例")
    print("=" * 50)
    
    # 创建客户端
    client = BilibiliAnalyzerClient()
    
    try:
        # 1. 检查服务状态
        print("1. 检查服务状态...")
        health = client.check_health()
        if health['success']:
            print(f"✅ 服务状态: {health['data']['status']}")
        else:
            print(f"❌ 服务异常: {health['message']}")
            return
        
        # 2. 获取系统信息
        print("\n2. 获取系统信息...")
        info = client.get_system_info()
        if info['success']:
            print(f"✅ API名称: {info['data']['name']}")
            print(f"✅ API版本: {info['data']['version']}")
        
        # 3. 获取系统统计
        print("\n3. 获取系统统计...")
        stats = client.get_system_stats()
        if stats['success']:
            data = stats['data']['overview']
            print(f"✅ 视频总数: {data['total_videos']}")
            print(f"✅ 分析总数: {data['total_analyses']}")
            print(f"✅ 知识条目: {data['total_knowledge_entries']}")
            print(f"✅ 标签总数: {data['total_tags']}")
        
        # 4. 获取标签列表
        print("\n4. 获取标签列表...")
        tags = client.get_tags(page=1, per_page=5)
        if tags['success']:
            print("✅ 标签列表:")
            for tag in tags['data']['items']:
                print(f"   - {tag['name']} ({tag['usage_count']}次使用)")
        
        # 5. 获取知识条目
        print("\n5. 获取知识条目...")
        knowledge = client.get_knowledge_entries(page=1, per_page=3)
        if knowledge['success']:
            print("✅ 知识条目:")
            for entry in knowledge['data']['items']:
                print(f"   - {entry['title']} ({entry['knowledge_type']})")
        
        print("\n🎉 基本功能演示完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保服务正在运行")
        print("💡 运行命令: python app.py")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def demo_video_analysis():
    """演示视频分析功能"""
    print("\n🎬 视频分析功能演示")
    print("=" * 50)
    
    # 创建客户端
    client = BilibiliAnalyzerClient()
    
    # 使用一个示例BV号（实际使用时请替换为真实有效的BV号）
    demo_bvid = "BV1GJ411x7h7"
    
    try:
        # 1. 提取视频信息
        print(f"1. 提取视频信息 ({demo_bvid})...")
        video_info = client.extract_video_info(demo_bvid)
        
        if video_info['success']:
            data = video_info['data']
            print(f"✅ 视频标题: {data['video_info']['title']}")
            print(f"✅ 视频作者: {data['video_info']['author']}")
            print(f"✅ 视频时长: {data['video_info']['duration']}秒")
            print(f"✅ 字幕可用: {'是' if data['subtitle_available'] else '否'}")
        else:
            print(f"❌ 提取失败: {video_info['message']}")
            return
        
        # 2. 下载字幕
        print("\n2. 下载字幕...")
        subtitle = client.download_subtitle(demo_bvid)
        
        if subtitle['success']:
            data = subtitle['data']
            print(f"✅ 字幕语言: {data['subtitle']['language']}")
            print(f"✅ 字幕格式: {data['subtitle']['format']}")
            print(f"✅ 字幕行数: {data['subtitle']['line_count']}")
        else:
            print(f"❌ 字幕下载失败: {subtitle['message']}")
        
        # 3. 分析内容
        print("\n3. 分析内容...")
        analysis = client.analyze_content(demo_bvid, force_reanalyze=True)
        
        if analysis['success']:
            data = analysis['data']
            print(f"✅ 分析完成，使用模型: {data['analysis']['model_used']}")
            print(f"✅ 分析耗时: {data['analysis']['analysis_time']:.2f}秒")
            print(f"✅ 知识条目数: {len(data['knowledge_entries'])}")
            print(f"✅ 分析总结: {data['analysis']['summary'][:100]}...")
        else:
            print(f"❌ 分析失败: {analysis['message']}")
        
        print("\n🎉 视频分析演示完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保服务正在运行")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def demo_knowledge_management():
    """演示知识库管理功能"""
    print("\n📚 知识库管理功能演示")
    print("=" * 50)
    
    # 创建客户端
    client = BilibiliAnalyzerClient()
    
    try:
        # 1. 创建标签
        print("1. 创建标签...")
        tag_names = ["Python", "机器学习", "编程", "示例"]
        created_tags = []
        
        for tag_name in tag_names:
            tag = client.create_tag(tag_name)
            if tag['success']:
                print(f"✅ 创建标签: {tag['data']['name']}")
                created_tags.append(tag['data'])
            else:
                print(f"⚠️  标签可能已存在: {tag_name}")
        
        # 2. 创建知识条目
        print("\n2. 创建知识条目...")
        entries_data = [
            {
                "title": "Python基础语法",
                "content": "Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。Python支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。",
                "knowledge_type": "concept",
                "importance": 4,
                "tags": ["Python", "编程"]
            },
            {
                "title": "机器学习概述",
                "content": "机器学习是人工智能的一个分支，它使计算机能够从数据中学习并改进性能，而无需明确编程。机器学习算法通过识别数据中的模式来进行预测和决策。",
                "knowledge_type": "concept",
                "importance": 5,
                "tags": ["机器学习", "AI"]
            },
            {
                "title": "RESTful API设计原则",
                "content": "RESTful API是一种基于REST架构风格的API设计方法。它使用HTTP方法（GET、POST、PUT、DELETE）来执行CRUD操作，并使用JSON格式进行数据交换。",
                "knowledge_type": "method",
                "importance": 3,
                "tags": ["编程", "示例"]
            }
        ]
        
        created_entries = []
        for entry_data in entries_data:
            entry = client.create_knowledge_entry(**entry_data)
            if entry['success']:
                print(f"✅ 创建知识条目: {entry['data']['title']}")
                created_entries.append(entry['data'])
            else:
                print(f"❌ 创建失败: {entry['message']}")
        
        # 3. 搜索知识库
        print("\n3. 搜索知识库...")
        search_results = client.search_knowledge("Python", limit=5)
        
        if search_results['success']:
            results = search_results['data']['results']
            print(f"✅ 搜索到 {len(results)} 个结果:")
            for result in results:
                print(f"   - {result['title']} (相关性: {result.get('relevance_score', 0):.2f})")
        
        # 4. 获取知识条目列表
        print("\n4. 获取知识条目列表...")
        knowledge_list = client.get_knowledge_entries(page=1, per_page=5)
        
        if knowledge_list['success']:
            items = knowledge_list['data']['items']
            pagination = knowledge_list['data']['pagination']
            print(f"✅ 共 {pagination['total']} 个知识条目，显示第 {pagination['page']} 页:")
            for item in items:
                print(f"   - {item['title']} ({item['knowledge_type']}, 重要性: {item['importance']})")
        
        print("\n🎉 知识库管理演示完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保服务正在运行")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def demo_performance_monitoring():
    """演示性能监控功能"""
    print("\n📊 性能监控功能演示")
    print("=" * 50)
    
    # 创建客户端
    client = BilibiliAnalyzerClient()
    
    try:
        # 1. 测试健康检查响应时间
        print("1. 测试健康检查响应时间...")
        times = []
        for i in range(5):
            start_time = time.time()
            client.check_health()
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        print(f"✅ 健康检查平均响应时间: {avg_time:.3f}秒")
        
        # 2. 获取系统统计
        print("\n2. 获取系统统计...")
        stats = client.get_system_stats()
        if stats['success']:
            data = stats['data']
            print(f"✅ 视频覆盖率: {data['overview']['subtitle_coverage']:.1f}%")
            print(f"✅ 分析覆盖率: {data['overview']['analysis_coverage']:.1f}%")
            print(f"✅ 平均分析时间: {data['analysis_stats']['avg_analysis_time']:.2f}秒")
        
        # 3. 获取详细健康状态
        print("\n3. 获取详细健康状态...")
        health_response = client.session.get(f"{client.base_url}/api/v1/health/detailed")
        detailed_health = health_response.json()
        
        if detailed_health['success']:
            data = detailed_health['data']
            print(f"✅ 系统状态: {data['status']}")
            print(f"✅ 数据库状态: {data['components']['database']['status']}")
            print(f"✅ 数据库表状态: {data['components']['database_tables']['status']}")
        
        print("\n🎉 性能监控演示完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保服务正在运行")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

def main():
    """主函数"""
    print("🚀 Bilibili视频分析系统API - 完整功能演示")
    print("=" * 60)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 运行所有演示
    demo_basic_usage()
    demo_video_analysis()
    demo_knowledge_management()
    demo_performance_monitoring()
    
    print("\n" + "=" * 60)
    print("🎉 所有演示完成！")
    print("=" * 60)
    print("💡 提示:")
    print("   - 查看完整API文档: http://localhost:5000/api/docs")
    print("   - 运行性能测试: python test_api_performance.py")
    print("   - 运行功能测试: python test_api.py")
    print("   - 验证API状态: python validate_api.py")

if __name__ == "__main__":
    main()