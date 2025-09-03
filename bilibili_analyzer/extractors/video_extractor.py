"""
Bilibili视频分析系统 - 视频信息提取器
"""

import json
import re
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urljoin
import requests

from .models import (
    VideoInfo, Subtitle, SubtitleLine, SubtitleInfo, SubtitleFormat,
    ExtractionError, VideoNotFoundError, SubtitleNotFoundError,
    NetworkError, ParseError, RateLimitError
)
from ..utils import get_json, get_text, get_request_handler

class VideoExtractor:
    """B站视频信息提取器"""
    
    # B站API端点
    API_BASE = "https://api.bilibili.com"
    VIDEO_INFO_URL = f"{API_BASE}/x/web-interface/view"
    SUBTITLE_URL = f"{API_BASE}/x/player/v2"
    
    # B站主站
    MAIN_BASE = "https://www.bilibili.com"
    
    def __init__(self, delay_range: tuple = (1, 3)):
        """
        初始化提取器
        
        Args:
            delay_range: 请求延迟范围（最小，最大）秒
        """
        self.request_handler = get_request_handler()
        
    def extract_video_info(self, bvid: str) -> VideoInfo:
        """
        提取视频信息
        
        Args:
            bvid: B站视频ID
            
        Returns:
            视频信息对象
            
        Raises:
            VideoNotFoundError: 视频未找到
            NetworkError: 网络错误
            ParseError: 解析错误
            RateLimitError: 请求频率限制
        """
        try:
            # 调用B站API获取视频信息
            params = {'bvid': bvid}
            response = get_json(self.VIDEO_INFO_URL, params=params)
            
            # 检查API响应
            if response.get('code') != 0:
                error_msg = response.get('message', '未知错误')
                if '不存在' in error_msg or '找不到' in error_msg:
                    raise VideoNotFoundError(f"视频不存在: {bvid}")
                elif '请求过于频繁' in error_msg or '访问频率' in error_msg:
                    raise RateLimitError(f"请求频率限制: {error_msg}")
                else:
                    raise ExtractionError(f"API错误: {error_msg}")
            
            data = response.get('data', {})
            
            # 解析发布时间
            publish_date = None
            if 'pubdate' in data and data['pubdate']:
                publish_date = datetime.fromtimestamp(data['pubdate'])
            
            # 创建视频信息对象
            video_info = VideoInfo(
                bvid=bvid,
                title=data.get('title', '').strip(),
                author=data.get('owner', {}).get('name', ''),
                duration=data.get('duration', 0),
                publish_date=publish_date,
                thumbnail_url=data.get('pic', ''),
                description=data.get('desc', ''),
                view_count=data.get('stat', {}).get('view', 0),
                like_count=data.get('stat', {}).get('like', 0),
                coin_count=data.get('stat', {}).get('coin', 0),
                favorite_count=data.get('stat', {}).get('favorite', 0),
                share_count=data.get('stat', {}).get('share', 0),
                cid=data.get('cid')
            )
            
            return video_info
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"网络请求失败: {str(e)}")
        except (ValueError, KeyError, TypeError) as e:
            raise ParseError(f"数据解析失败: {str(e)}")
        except Exception as e:
            if isinstance(e, (VideoNotFoundError, NetworkError, ParseError, RateLimitError)):
                raise
            raise ExtractionError(f"提取视频信息失败: {str(e)}")
    
    def check_subtitle_available(self, bvid: str) -> bool:
        """
        检查字幕是否可用
        
        Args:
            bvid: B站视频ID
            
        Returns:
            是否有字幕
            
        Raises:
            VideoNotFoundError: 视频未找到
            NetworkError: 网络错误
        """
        try:
            # 先获取视频信息得到cid
            video_info = self.extract_video_info(bvid)
            if not video_info.cid:
                return False
            
            # 获取字幕信息
            params = {'bvid': bvid, 'cid': video_info.cid}
            response = get_json(self.SUBTITLE_URL, params=params)
            
            if response.get('code') != 0:
                return False
            
            data = response.get('data', {})
            subtitle_info = data.get('subtitle', {})
            
            # 检查是否有字幕
            subtitles = subtitle_info.get('subtitles', [])
            return len(subtitles) > 0
            
        except (VideoNotFoundError, NetworkError):
            raise
        except Exception as e:
            # 其他错误视为无字幕
            return False
    
    def get_subtitle_list(self, bvid: str) -> List[SubtitleInfo]:
        """
        获取字幕列表
        
        Args:
            bvid: B站视频ID
            
        Returns:
            字幕信息列表
            
        Raises:
            VideoNotFoundError: 视频未找到
            SubtitleNotFoundError: 字幕未找到
            NetworkError: 网络错误
        """
        try:
            # 获取视频信息得到cid
            video_info = self.extract_video_info(bvid)
            if not video_info.cid:
                raise SubtitleNotFoundError("无法获取视频CID")
            
            # 获取字幕信息
            params = {'bvid': bvid, 'cid': video_info.cid}
            response = get_json(self.SUBTITLE_URL, params=params)
            
            if response.get('code') != 0:
                raise SubtitleNotFoundError("获取字幕信息失败")
            
            data = response.get('data', {})
            subtitle_info = data.get('subtitle', {})
            subtitles = subtitle_info.get('subtitles', [])
            
            if not subtitles:
                raise SubtitleNotFoundError("该视频没有字幕")
            
            # 转换为SubtitleInfo对象
            subtitle_list = []
            for sub in subtitles:
                subtitle_info_obj = SubtitleInfo(
                    id=sub.get('id', 0),
                    lan=sub.get('lan', ''),
                    lan_doc=sub.get('lan_doc', ''),
                    is_login=sub.get('is_login', False),
                    subtitle_url=sub.get('subtitle_url', '')
                )
                subtitle_list.append(subtitle_info_obj)
            
            return subtitle_list
            
        except (VideoNotFoundError, SubtitleNotFoundError, NetworkError):
            raise
        except Exception as e:
            if isinstance(e, (VideoNotFoundError, NetworkError)):
                raise
            raise SubtitleNotFoundError(f"获取字幕列表失败: {str(e)}")
    
    def download_subtitle(self, bvid: str, language: str = 'zh-CN') -> Subtitle:
        """
        下载字幕
        
        Args:
            bvid: B站视频ID
            language: 语言代码，默认为中文
            
        Returns:
            字幕对象
            
        Raises:
            VideoNotFoundError: 视频未找到
            SubtitleNotFoundError: 字幕未找到
            NetworkError: 网络错误
            ParseError: 解析错误
        """
        try:
            # 获取字幕列表
            subtitle_list = self.get_subtitle_list(bvid)
            
            # 查找指定语言的字幕
            target_subtitle = None
            for sub in subtitle_list:
                if sub.lan == language or sub.lan_doc == language:
                    target_subtitle = sub
                    break
            
            if not target_subtitle:
                # 如果找不到指定语言，使用第一个可用字幕
                if subtitle_list:
                    target_subtitle = subtitle_list[0]
                else:
                    raise SubtitleNotFoundError(f"找不到语言为 {language} 的字幕")
            
            # 下载字幕内容
            subtitle_url = target_subtitle.subtitle_url
            if not subtitle_url:
                raise SubtitleNotFoundError("字幕URL为空")
            
            # 处理相对URL
            if not subtitle_url.startswith(('http://', 'https://')):
                subtitle_url = urljoin(self.MAIN_BASE, subtitle_url)
            
            content = get_text(subtitle_url)
            
            # 解析字幕内容
            lines = self.parse_subtitle_content(content, 'json')
            
            # 创建字幕对象
            subtitle = Subtitle(
                video_id=bvid,
                language=target_subtitle.lan,
                format='json',
                lines=lines,
                content=content
            )
            
            return subtitle
            
        except (VideoNotFoundError, SubtitleNotFoundError, NetworkError, ParseError):
            raise
        except Exception as e:
            raise SubtitleNotFoundError(f"下载字幕失败: {str(e)}")
    
    def parse_subtitle_content(self, content: str, format_name: str) -> List[SubtitleLine]:
        """
        解析字幕内容
        
        Args:
            content: 字幕内容
            format_name: 字幕格式
            
        Returns:
            字幕行列表
            
        Raises:
            ParseError: 解析错误
        """
        try:
            format_name = format_name.lower()
            
            if format_name == 'json':
                return self._parse_json_subtitle(content)
            elif format_name == 'xml':
                return self._parse_xml_subtitle(content)
            elif format_name == 'srt':
                return self._parse_srt_subtitle(content)
            elif format_name == 'vtt':
                return self._parse_vtt_subtitle(content)
            else:
                raise ParseError(f"不支持的字幕格式: {format_name}")
                
        except Exception as e:
            raise ParseError(f"解析字幕内容失败: {str(e)}")
    
    def _parse_json_subtitle(self, content: str) -> List[SubtitleLine]:
        """解析JSON格式字幕"""
        try:
            data = json.loads(content)
            lines = []
            
            # B站JSON字幕格式
            if 'body' in data:
                for i, item in enumerate(data['body']):
                    line = SubtitleLine(
                        start_time=float(item.get('from', 0)),
                        end_time=float(item.get('to', 0)),
                        text=item.get('content', ''),
                        index=i
                    )
                    lines.append(line)
            
            return lines
            
        except json.JSONDecodeError as e:
            raise ParseError(f"JSON解析失败: {str(e)}")
    
    def _parse_xml_subtitle(self, content: str) -> List[SubtitleLine]:
        """解析XML格式字幕"""
        try:
            root = ET.fromstring(content)
            lines = []
            
            # 解析XML字幕格式
            for i, subtitle in enumerate(root.findall('.//subtitle')):
                start_time = float(subtitle.get('start_time', 0))
                end_time = float(subtitle.get('end_time', 0))
                text = subtitle.text or ''
                
                line = SubtitleLine(
                    start_time=start_time,
                    end_time=end_time,
                    text=text,
                    index=i
                )
                lines.append(line)
            
            return lines
            
        except ET.ParseError as e:
            raise ParseError(f"XML解析失败: {str(e)}")
    
    def _parse_srt_subtitle(self, content: str) -> List[SubtitleLine]:
        """解析SRT格式字幕"""
        lines = []
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for i, block in enumerate(blocks):
            if not block.strip():
                continue
            
            parts = block.strip().split('\n')
            if len(parts) < 2:
                continue
            
            # 解析时间戳
            time_line = parts[1]
            time_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
            if not time_match:
                continue
            
            start_time = self._parse_srt_time(time_match.group(1))
            end_time = self._parse_srt_time(time_match.group(2))
            
            # 解析文本
            text = '\n'.join(parts[2:]) if len(parts) > 2 else ''
            
            line = SubtitleLine(
                start_time=start_time,
                end_time=end_time,
                text=text,
                index=i
            )
            lines.append(line)
        
        return lines
    
    def _parse_vtt_subtitle(self, content: str) -> List[SubtitleLine]:
        """解析VTT格式字幕"""
        lines = []
        content = content.replace('\r\n', '\n')
        blocks = content.split('\n\n')
        
        # 跳过头部
        start_index = 0
        for i, block in enumerate(blocks):
            if block.strip() == 'WEBVTT':
                start_index = i + 1
                break
        
        for i, block in enumerate(blocks[start_index:], start_index):
            if not block.strip():
                continue
            
            parts = block.strip().split('\n')
            if len(parts) < 2:
                continue
            
            # 解析时间戳
            time_line = parts[0]
            time_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})', time_line)
            if not time_match:
                continue
            
            start_time = self._parse_vtt_time(time_match.group(1))
            end_time = self._parse_vtt_time(time_match.group(2))
            
            # 解析文本
            text = '\n'.join(parts[1:]) if len(parts) > 1 else ''
            
            line = SubtitleLine(
                start_time=start_time,
                end_time=end_time,
                text=text,
                index=i
            )
            lines.append(line)
        
        return lines
    
    def _parse_srt_time(self, time_str: str) -> float:
        """解析SRT时间格式"""
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split(',')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    
    def _parse_vtt_time(self, time_str: str) -> float:
        """解析VTT时间格式"""
        h, m, s_ms = time_str.split(':')
        s, ms = s_ms.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000
    
    def extract_all(self, bvid: str, language: str = 'zh-CN') -> Dict[str, Any]:
        """
        提取视频信息和字幕
        
        Args:
            bvid: B站视频ID
            language: 字幕语言
            
        Returns:
            包含视频信息和字幕的字典
        """
        result = {
            'video_info': None,
            'subtitle': None,
            'subtitle_available': False
        }
        
        try:
            # 提取视频信息
            result['video_info'] = self.extract_video_info(bvid)
            
            # 检查字幕
            result['subtitle_available'] = self.check_subtitle_available(bvid)
            
            if result['subtitle_available']:
                try:
                    result['subtitle'] = self.download_subtitle(bvid, language)
                except SubtitleNotFoundError:
                    result['subtitle_available'] = False
            
        except Exception as e:
            raise ExtractionError(f"提取视频信息失败: {str(e)}")
        
        return result