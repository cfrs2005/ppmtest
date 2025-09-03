"""
Bilibili视频分析系统 - 视频提取器测试
"""

import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from bilibili_analyzer.extractors import (
    VideoExtractor, VideoInfo, Subtitle, SubtitleLine, SubtitleFormat,
    VideoNotFoundError, SubtitleNotFoundError, NetworkError, ParseError
)
from bilibili_analyzer.services import DatabaseService

class TestVideoExtractor(unittest.TestCase):
    """视频提取器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.extractor = VideoExtractor(delay_range=(0, 0))  # 测试时不延迟
        
    def test_parse_srt_time(self):
        """测试SRT时间解析"""
        # 测试标准SRT时间格式
        time_str = "00:01:30,500"
        result = self.extractor._parse_srt_time(time_str)
        self.assertEqual(result, 90.5)
        
        # 测试边界情况
        time_str = "00:00:00,000"
        result = self.extractor._parse_srt_time(time_str)
        self.assertEqual(result, 0.0)
        
        time_str = "01:00:00,000"
        result = self.extractor._parse_srt_time(time_str)
        self.assertEqual(result, 3600.0)
    
    def test_parse_vtt_time(self):
        """测试VTT时间解析"""
        # 测试标准VTT时间格式
        time_str = "00:01:30.500"
        result = self.extractor._parse_vtt_time(time_str)
        self.assertEqual(result, 90.5)
        
        # 测试边界情况
        time_str = "00:00:00.000"
        result = self.extractor._parse_vtt_time(time_str)
        self.assertEqual(result, 0.0)
    
    def test_parse_json_subtitle(self):
        """测试JSON字幕解析"""
        # 模拟B站JSON字幕格式
        json_content = json.dumps({
            "body": [
                {
                    "from": 0.0,
                    "to": 5.0,
                    "content": "这是第一行字幕"
                },
                {
                    "from": 5.0,
                    "to": 10.0,
                    "content": "这是第二行字幕"
                }
            ]
        })
        
        lines = self.extractor._parse_json_subtitle(json_content)
        
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].text, "这是第一行字幕")
        self.assertEqual(lines[0].start_time, 0.0)
        self.assertEqual(lines[0].end_time, 5.0)
        self.assertEqual(lines[1].text, "这是第二行字幕")
        self.assertEqual(lines[1].start_time, 5.0)
        self.assertEqual(lines[1].end_time, 10.0)
    
    def test_parse_srt_subtitle(self):
        """测试SRT字幕解析"""
        srt_content = """1
00:00:00,000 --> 00:00:05,000
这是第一行字幕

2
00:00:05,000 --> 00:00:10,000
这是第二行字幕"""
        
        lines = self.extractor._parse_srt_subtitle(srt_content)
        
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].text, "这是第一行字幕")
        self.assertEqual(lines[0].start_time, 0.0)
        self.assertEqual(lines[0].end_time, 5.0)
        self.assertEqual(lines[1].text, "这是第二行字幕")
        self.assertEqual(lines[1].start_time, 5.0)
        self.assertEqual(lines[1].end_time, 10.0)
    
    def test_parse_vtt_subtitle(self):
        """测试VTT字幕解析"""
        vtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
这是第一行字幕

00:00:05.000 --> 00:00:10.000
这是第二行字幕"""
        
        lines = self.extractor._parse_vtt_subtitle(vtt_content)
        
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].text, "这是第一行字幕")
        self.assertEqual(lines[0].start_time, 0.0)
        self.assertEqual(lines[0].end_time, 5.0)
        self.assertEqual(lines[1].text, "这是第二行字幕")
        self.assertEqual(lines[1].start_time, 5.0)
        self.assertEqual(lines[1].end_time, 10.0)
    
    def test_parse_subtitle_content(self):
        """测试字幕内容解析"""
        # 测试JSON格式
        json_content = json.dumps({
            "body": [{"from": 0.0, "to": 5.0, "content": "测试字幕"}]
        })
        lines = self.extractor.parse_subtitle_content(json_content, 'json')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].text, "测试字幕")
        
        # 测试SRT格式
        srt_content = "1\n00:00:00,000 --> 00:00:05,000\n测试字幕"
        lines = self.extractor.parse_subtitle_content(srt_content, 'srt')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].text, "测试字幕")
        
        # 测试VTT格式
        vtt_content = "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\n测试字幕"
        lines = self.extractor.parse_subtitle_content(vtt_content, 'vtt')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].text, "测试字幕")
        
        # 测试不支持的格式
        with self.assertRaises(ParseError):
            self.extractor.parse_subtitle_content("test", "unsupported")
    
    def test_subtitle_format(self):
        """测试字幕格式工具"""
        # 测试支持的格式
        self.assertTrue(SubtitleFormat.is_supported('json'))
        self.assertTrue(SubtitleFormat.is_supported('xml'))
        self.assertTrue(SubtitleFormat.is_supported('srt'))
        self.assertTrue(SubtitleFormat.is_supported('vtt'))
        
        # 测试不支持的格式
        self.assertFalse(SubtitleFormat.is_supported('txt'))
        self.assertFalse(SubtitleFormat.is_supported('ass'))
        
        # 测试获取支持的格式
        formats = SubtitleFormat.get_supported_formats()
        self.assertIn('json', formats)
        self.assertIn('srt', formats)
        self.assertIn('vtt', formats)
    
    def test_video_info_to_dict(self):
        """测试视频信息转换为字典"""
        video_info = VideoInfo(
            bvid="BV1234567890",
            title="测试视频",
            author="测试作者",
            duration=300,
            publish_date=datetime(2023, 1, 1, 12, 0, 0),
            thumbnail_url="https://example.com/thumb.jpg",
            view_count=1000,
            like_count=100
        )
        
        result = video_info.to_dict()
        
        self.assertEqual(result['bvid'], "BV1234567890")
        self.assertEqual(result['title'], "测试视频")
        self.assertEqual(result['author'], "测试作者")
        self.assertEqual(result['duration'], 300)
        self.assertEqual(result['view_count'], 1000)
        self.assertEqual(result['like_count'], 100)
    
    def test_subtitle_line_to_dict(self):
        """测试字幕行转换为字典"""
        line = SubtitleLine(
            start_time=0.0,
            end_time=5.0,
            text="测试字幕",
            index=1
        )
        
        result = line.to_dict()
        
        self.assertEqual(result['start_time'], 0.0)
        self.assertEqual(result['end_time'], 5.0)
        self.assertEqual(result['text'], "测试字幕")
        self.assertEqual(result['index'], 1)
    
    @patch('bilibili_analyzer.extractors.video_extractor.get_json')
    def test_extract_video_info_success(self, mock_get_json):
        """测试成功提取视频信息"""
        # 模拟API响应
        mock_response = {
            'code': 0,
            'data': {
                'title': '测试视频',
                'owner': {'name': '测试作者'},
                'duration': 300,
                'pubdate': 1672531200,  # 2023-01-01 00:00:00
                'pic': 'https://example.com/thumb.jpg',
                'desc': '测试描述',
                'stat': {
                    'view': 1000,
                    'like': 100,
                    'coin': 50,
                    'favorite': 25,
                    'share': 10
                },
                'cid': 123456789
            }
        }
        mock_get_json.return_value = mock_response
        
        result = self.extractor.extract_video_info('BV1234567890')
        
        self.assertIsInstance(result, VideoInfo)
        self.assertEqual(result.title, '测试视频')
        self.assertEqual(result.author, '测试作者')
        self.assertEqual(result.duration, 300)
        self.assertEqual(result.view_count, 1000)
        self.assertEqual(result.like_count, 100)
        self.assertEqual(result.cid, 123456789)
    
    @patch('bilibili_analyzer.extractors.video_extractor.get_json')
    def test_extract_video_info_not_found(self, mock_get_json):
        """测试视频不存在的情况"""
        mock_response = {
            'code': -404,
            'message': '视频不存在'
        }
        mock_get_json.return_value = mock_response
        
        with self.assertRaises(VideoNotFoundError):
            self.extractor.extract_video_info('BV1234567890')
    
    @patch('bilibili_analyzer.extractors.video_extractor.get_json')
    def test_extract_video_info_rate_limit(self, mock_get_json):
        """测试请求频率限制"""
        mock_response = {
            'code': -412,
            'message': '请求过于频繁'
        }
        mock_get_json.return_value = mock_response
        
        with self.assertRaises(Exception):  # 应该抛出RateLimitError
            self.extractor.extract_video_info('BV1234567890')

class TestDatabaseService(unittest.TestCase):
    """数据库服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.service = DatabaseService()
        
    def test_video_info_to_dict(self):
        """测试视频信息数据类"""
        video_info = VideoInfo(
            bvid="BV1234567890",
            title="测试视频",
            author="测试作者",
            duration=300,
            publish_date=datetime(2023, 1, 1, 12, 0, 0),
            thumbnail_url="https://example.com/thumb.jpg"
        )
        
        result = video_info.to_dict()
        
        self.assertEqual(result['bvid'], "BV1234567890")
        self.assertEqual(result['title'], "测试视频")
        self.assertEqual(result['author'], "测试作者")
        self.assertEqual(result['duration'], 300)
    
    def test_subtitle_line_to_dict(self):
        """测试字幕行数据类"""
        line = SubtitleLine(
            start_time=0.0,
            end_time=5.0,
            text="测试字幕",
            index=1
        )
        
        result = line.to_dict()
        
        self.assertEqual(result['start_time'], 0.0)
        self.assertEqual(result['end_time'], 5.0)
        self.assertEqual(result['text'], "测试字幕")
        self.assertEqual(result['index'], 1)

class TestUtils(unittest.TestCase):
    """工具类测试"""
    
    def test_subtitle_format(self):
        """测试字幕格式工具"""
        # 测试支持的格式
        self.assertTrue(SubtitleFormat.is_supported('json'))
        self.assertTrue(SubtitleFormat.is_supported('srt'))
        self.assertTrue(SubtitleFormat.is_supported('vtt'))
        
        # 测试不支持的格式
        self.assertFalse(SubtitleFormat.is_supported('txt'))
        self.assertFalse(SubtitleFormat.is_supported('ass'))
    
    def test_subtitle_format_list(self):
        """测试获取支持的格式列表"""
        formats = SubtitleFormat.get_supported_formats()
        self.assertIsInstance(formats, list)
        self.assertIn('json', formats)
        self.assertIn('srt', formats)
        self.assertIn('vtt', formats)

if __name__ == '__main__':
    unittest.main()