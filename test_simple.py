#!/usr/bin/env python3
"""
简化的Bilibili视频分析测试脚本
"""

import sys
import os
sys.path.insert(0, '/workspace')

# 添加虚拟环境路径
venv_python = '/workspace/venv/bin/python'
if os.path.exists(venv_python):
    os.environ['PYTHONPATH'] = '/workspace'

def test_video_extraction():
    """测试视频信息提取"""
    print("🧪 测试视频信息提取...")
    
    # 测试视频BV号
    test_bvid = "BV1GJ411x7h7"
    
    try:
        # 直接导入测试
        from bilibili_analyzer.extractors.video_extractor import VideoExtractor
        extractor = VideoExtractor()
        print(f"📹 正在提取视频信息: {test_bvid}")
        
        # 提取视频信息
        video_info = extractor.extract_video_info(test_bvid)
        print(f"✅ 视频标题: {video_info.title}")
        print(f"✅ 视频作者: {video_info.author}")
        print(f"✅ 视频时长: {video_info.duration}秒")
        
        # 检查字幕可用性
        subtitle_available = extractor.check_subtitle_available(test_bvid)
        print(f"✅ 字幕可用: {subtitle_available}")
        
        if subtitle_available:
            # 下载字幕
            subtitle = extractor.download_subtitle(test_bvid)
            print(f"✅ 字幕语言: {subtitle.language}")
            print(f"✅ 字幕内容长度: {len(subtitle.content)}字符")
            
            return video_info, subtitle
        else:
            print("❌ 字幕不可用")
            return video_info, None
            
    except Exception as e:
        print(f"❌ 视频提取失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_content_analysis_simple(subtitle):
    """简化的内容分析测试"""
    if not subtitle:
        print("⏭️  跳过内容分析测试（无字幕）")
        return
    
    print("\n🧪 测试内容分析（简化版本）...")
    
    try:
        # 简单分析字幕内容
        content = subtitle.content
        
        # 基本统计
        char_count = len(content)
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        print(f"✅ 字幕统计:")
        print(f"   字符数: {char_count}")
        print(f"   单词数: {word_count}")
        print(f"   行数: {line_count}")
        
        # 简单的关键词提取（基于词频）
        import re
        from collections import Counter
        
        # 移除标点符号和数字
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = Counter(words)
        
        # 过滤常见词
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'a', 'an', '的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '这', '那', '个', '一', '不', '就', '还', '也', '都', '要', '说', '上', '来', '去', '过', '能', '会', '可以', '没有', '什么', '时候', '所以', '因为', '如果', '虽然', '但是', '而且', '或者', '可是', '然而', '因此', '于是', '接着', '然后', '最后', '首先', '其次', '再次', '另外', '此外', '除了', '包括', '比如', '例如', '以及', '而且', '并且', '同时', '之后', '之前', '当中', '里面', '外面', '上面', '下面', '左边', '右边', '前面', '后面'}
        
        # 获取前10个高频词
        keywords = [word for word, count in word_freq.most_common(20) if word not in common_words and len(word) > 1][:10]
        
        print(f"✅ 关键词: {keywords}")
        
        # 生成简单摘要（取前100个字符）
        summary = content[:100] + "..." if len(content) > 100 else content
        print(f"✅ 内容摘要: {summary}")
        
        return {
            'summary': summary,
            'keywords': keywords,
            'stats': {
                'char_count': char_count,
                'word_count': word_count,
                'line_count': line_count
            }
        }
        
    except Exception as e:
        print(f"❌ 内容分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_api_endpoints():
    """测试API端点"""
    print("\n🧪 测试API端点...")
    
    import requests
    import time
    
    # 等待应用启动
    print("⏳ 等待应用启动...")
    time.sleep(2)
    
    base_url = "http://localhost:5000"
    
    endpoints = [
        ("/", "首页"),
        ("/api/v1/health", "健康检查"),
        ("/api/v1/videos", "视频列表"),
        ("/api/v1/analysis", "分析结果"),
        ("/api/v1/knowledge", "知识库"),
        ("/api/v1/stats", "统计信息"),
        ("/dashboard", "仪表板")
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        try:
            url = base_url + endpoint
            response = requests.get(url, timeout=5)
            print(f"✅ {name} ({endpoint}): {response.status_code}")
            results[endpoint] = {
                'status': response.status_code,
                'success': response.status_code < 400
            }
        except Exception as e:
            print(f"❌ {name} ({endpoint}): {e}")
            results[endpoint] = {
                'status': 'error',
                'success': False,
                'error': str(e)
            }
    
    return results

def main():
    """主测试函数"""
    print("🚀 Bilibili视频分析系统 - 功能测试")
    print("=" * 50)
    
    # 测试视频信息提取
    video_info, subtitle = test_video_extraction()
    
    # 测试内容分析
    if subtitle:
        analysis_result = test_content_analysis_simple(subtitle)
    
    # 测试API端点
    api_results = test_api_endpoints()
    
    print("\n📊 测试总结:")
    print("=" * 50)
    print(f"✅ 视频信息提取: {'成功' if video_info else '失败'}")
    print(f"✅ 字幕下载: {'成功' if subtitle else '失败'}")
    print(f"✅ 内容分析: {'成功' if subtitle else '未测试'}")
    
    # API测试统计
    api_success = sum(1 for result in api_results.values() if result.get('success', False))
    api_total = len(api_results)
    print(f"✅ API端点测试: {api_success}/{api_total} 成功")
    
    if video_info:
        print(f"\n🎯 测试视频信息:")
        print(f"   标题: {video_info.title}")
        print(f"   作者: {video_info.author}")
        print(f"   时长: {video_info.duration}秒")
        print(f"   BV号: {video_info.bvid}")
    
    # API详细结果
    if api_results:
        print(f"\n🌐 API测试详情:")
        for endpoint, result in api_results.items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"   {status} {endpoint}: {result.get('status', 'error')}")

if __name__ == "__main__":
    main()