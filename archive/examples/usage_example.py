#!/usr/bin/env python3
"""
Bilibili视频信息提取模块 - 使用示例
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bilibili_analyzer.extractors import VideoExtractor, VideoNotFoundError
from bilibili_analyzer.services import DatabaseService
from bilibili_analyzer.utils import close_request_handler

def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建提取器
    extractor = VideoExtractor(delay_range=(1, 2))
    
    # 示例视频ID
    bvid = "BV1BW411j7y4"  # 一个公开的测试视频
    
    try:
        # 提取视频信息
        print(f"正在提取视频信息: {bvid}")
        video_info = extractor.extract_video_info(bvid)
        
        print(f"视频标题: {video_info.title}")
        print(f"视频作者: {video_info.author}")
        print(f"视频时长: {video_info.duration}秒")
        print(f"发布时间: {video_info.publish_date}")
        print(f"播放量: {video_info.view_count}")
        print(f"点赞数: {video_info.like_count}")
        
        # 检查字幕可用性
        print(f"\n检查字幕可用性...")
        subtitle_available = extractor.check_subtitle_available(bvid)
        print(f"字幕可用: {subtitle_available}")
        
        if subtitle_available:
            # 下载字幕
            print(f"\n下载字幕...")
            subtitle = extractor.download_subtitle(bvid, 'zh-CN')
            
            print(f"字幕语言: {subtitle.language}")
            print(f"字幕格式: {subtitle.format}")
            print(f"字幕行数: {len(subtitle.lines)}")
            
            # 显示前5行字幕
            print(f"\n前5行字幕:")
            for i, line in enumerate(subtitle.lines[:5]):
                print(f"  {i+1}. [{line.start_time:.1f}s-{line.end_time:.1f}s] {line.text}")
        
    except VideoNotFoundError:
        print(f"视频不存在: {bvid}")
    except Exception as e:
        print(f"提取失败: {str(e)}")

def example_subtitle_formats():
    """字幕格式示例"""
    print("\n=== 字幕格式示例 ===")
    
    extractor = VideoExtractor()
    
    # JSON格式示例
    json_content = '''{
        "body": [
            {"from": 0.0, "to": 5.0, "content": "欢迎观看本视频"},
            {"from": 5.0, "to": 10.0, "content": "今天我们来讲解Python编程"},
            {"from": 10.0, "to": 15.0, "content": "Python是一种简洁的编程语言"}
        ]
    }'''
    
    print("JSON格式解析:")
    lines = extractor.parse_subtitle_content(json_content, 'json')
    for line in lines:
        print(f"  [{line.start_time}s-{line.end_time}s] {line.text}")
    
    # SRT格式示例
    srt_content = '''1
00:00:00,000 --> 00:00:05,000
欢迎观看本视频

2
00:00:05,000 --> 00:00:10,000
今天我们来讲解Python编程

3
00:00:10,000 --> 00:00:15,000
Python是一种简洁的编程语言'''
    
    print("\nSRT格式解析:")
    lines = extractor.parse_subtitle_content(srt_content, 'srt')
    for line in lines:
        print(f"  [{line.start_time}s-{line.end_time}s] {line.text}")
    
    # VTT格式示例
    vtt_content = '''WEBVTT

00:00:00.000 --> 00:00:05.000
欢迎观看本视频

00:00:05.000 --> 00:00:10.000
今天我们来讲解Python编程

00:00:10.000 --> 00:00:15.000
Python是一种简洁的编程语言'''
    
    print("\nVTT格式解析:")
    lines = extractor.parse_subtitle_content(vtt_content, 'vtt')
    for line in lines:
        print(f"  [{line.start_time}s-{line.end_time}s] {line.text}")

def example_batch_processing():
    """批量处理示例"""
    print("\n=== 批量处理示例 ===")
    
    extractor = VideoExtractor(delay_range=(2, 3))
    
    # 示例视频列表
    test_videos = [
        "BV1BW411j7y4",
        "BV1GJ411x7h7",
    ]
    
    for bvid in test_videos:
        print(f"\n处理视频: {bvid}")
        
        try:
            # 使用提取所有信息的方法
            result = extractor.extract_all(bvid)
            
            if result['video_info']:
                video_info = result['video_info']
                print(f"  标题: {video_info.title}")
                print(f"  作者: {video_info.author}")
                print(f"  时长: {video_info.duration}秒")
            
            print(f"  字幕可用: {result['subtitle_available']}")
            
            if result['subtitle']:
                subtitle = result['subtitle']
                print(f"  字幕语言: {subtitle.language}")
                print(f"  字幕行数: {len(subtitle.lines)}")
            
        except Exception as e:
            print(f"  ❌ 处理失败: {str(e)}")

def example_database_integration():
    """数据库集成示例"""
    print("\n=== 数据库集成示例 ===")
    
    # 注意：这个示例需要配置好数据库
    print("数据库集成示例需要配置Flask应用和数据库")
    print("具体使用方法请参考bilibili_analyzer/services.py")
    
    # 示例代码结构
    example_code = '''
    from bilibili_analyzer.services import DatabaseService
    
    # 创建数据库服务
    service = DatabaseService()
    
    # 提取并保存视频信息
    result = service.extract_and_save_video(bvid, language='zh-CN')
    
    if result['success']:
        video = result['video']
        subtitle = result['subtitle']
        print(f"视频已保存: {video.title}")
        if subtitle:
            print(f"字幕已保存: {subtitle.language}")
    '''
    
    print("示例代码:")
    print(example_code)

def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    extractor = VideoExtractor(delay_range=(0, 0))
    
    # 测试各种错误情况
    test_cases = [
        ("无效视频ID", "invalid_bvid_format"),
        ("不存在视频", "BV123456789012345678901234567890"),
        ("无效JSON", "invalid json content"),
    ]
    
    for case_name, test_input in test_cases:
        print(f"\n测试{case_name}:")
        
        try:
            if case_name == "无效JSON":
                extractor.parse_subtitle_content(test_input, 'json')
            else:
                extractor.extract_video_info(test_input)
            print(f"  ❌ 应该抛出异常")
        except Exception as e:
            print(f"  ✅ 正确处理错误: {type(e).__name__}: {str(e)}")

def main():
    """主函数"""
    print("Bilibili视频信息提取模块 - 使用示例")
    print("=" * 60)
    
    try:
        # 运行各种示例
        example_basic_usage()
        example_subtitle_formats()
        example_batch_processing()
        example_database_integration()
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ 所有示例运行完成！")
        
        print("\n使用说明:")
        print("1. VideoExtractor类是主要的提取器")
        print("2. 支持的字幕格式: JSON, SRT, VTT")
        print("3. 内置反爬虫机制，自动处理延迟和User-Agent")
        print("4. 完整的错误处理机制")
        print("5. 可与数据库集成进行数据持久化")
        
    except KeyboardInterrupt:
        print("\n示例被用户中断")
    except Exception as e:
        print(f"\n示例运行失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        try:
            close_request_handler()
        except:
            pass

if __name__ == '__main__':
    main()