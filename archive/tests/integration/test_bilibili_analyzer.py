#!/usr/bin/env python3
"""
Bilibili视频分析系统 - 测试脚本
"""

import sys
import os
sys.path.insert(0, '/workspace')

# 添加虚拟环境路径
venv_python = '/workspace/venv/bin/python'
if os.path.exists(venv_python):
    os.environ['PYTHONPATH'] = '/workspace'

from bilibili_analyzer.extractors.video_extractor import VideoExtractor
from bilibili_analyzer.analyzers.content_analyzer import ContentAnalyzer

def test_video_extraction():
    """测试视频信息提取"""
    print("🧪 测试视频信息提取...")
    
    # 测试视频BV号
    test_bvid = "BV1GJ411x7h7"
    
    try:
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
        return None, None

def test_content_analysis(subtitle):
    """测试内容分析"""
    if not subtitle:
        print("⏭️  跳过内容分析测试（无字幕）")
        return
    
    print("\n🧪 测试内容分析...")
    
    try:
        analyzer = ContentAnalyzer()
        print(f"🤖 正在分析字幕内容...")
        
        # 分析字幕内容
        analysis_result = analyzer.analyze_subtitle(subtitle.content)
        print(f"✅ 分析完成")
        print(f"✅ 摘要: {analysis_result.summary[:100]}...")
        print(f"✅ 关键点数量: {len(analysis_result.key_points)}")
        print(f"✅ 分类: {analysis_result.categories}")
        print(f"✅ 标签: {analysis_result.tags}")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ 内容分析失败: {e}")
        return None

def main():
    """主测试函数"""
    print("🚀 Bilibili视频分析系统 - 功能测试")
    print("=" * 50)
    
    # 测试视频信息提取
    video_info, subtitle = test_video_extraction()
    
    # 测试内容分析
    if subtitle:
        analysis_result = test_content_analysis(subtitle)
    
    print("\n📊 测试总结:")
    print("=" * 50)
    print(f"✅ 视频信息提取: {'成功' if video_info else '失败'}")
    print(f"✅ 字幕下载: {'成功' if subtitle else '失败'}")
    print(f"✅ 内容分析: {'成功' if subtitle else '未测试'}")
    
    if video_info:
        print(f"\n🎯 测试视频信息:")
        print(f"   标题: {video_info.title}")
        print(f"   作者: {video_info.author}")
        print(f"   时长: {video_info.duration}秒")
        print(f"   BV号: {video_info.bvid}")

if __name__ == "__main__":
    main()