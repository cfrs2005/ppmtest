"""
Bilibili视频分析系统 - 视频提取数据模型
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class VideoInfo:
    """视频信息数据类"""
    bvid: str
    title: str
    author: str
    duration: int
    publish_date: Optional[datetime] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    coin_count: int = 0
    favorite_count: int = 0
    share_count: int = 0
    cid: Optional[int] = None  # 视频分P ID
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'bvid': self.bvid,
            'title': self.title,
            'author': self.author,
            'duration': self.duration,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'thumbnail_url': self.thumbnail_url,
            'description': self.description,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'coin_count': self.coin_count,
            'favorite_count': self.favorite_count,
            'share_count': self.share_count,
            'cid': self.cid
        }

@dataclass
class SubtitleLine:
    """字幕行数据类"""
    start_time: float  # 开始时间（秒）
    end_time: float    # 结束时间（秒）
    text: str          # 字幕文本
    index: int = 0     # 序号
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'text': self.text,
            'index': self.index
        }

@dataclass
class Subtitle:
    """字幕数据类"""
    video_id: str
    language: str
    format: str
    lines: List[SubtitleLine]
    content: str = ""
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'video_id': self.video_id,
            'language': self.language,
            'format': self.format,
            'lines': [line.to_dict() for line in self.lines],
            'content': self.content,
            'file_path': self.file_path
        }

@dataclass
class SubtitleInfo:
    """字幕信息数据类"""
    id: int
    lan: str          # 语言代码
    lan_doc: str      # 语言名称
    is_login: bool    # 是否需要登录
    subtitle_url: str # 字幕URL
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'lan': self.lan,
            'lan_doc': self.lan_doc,
            'is_login': self.is_login,
            'subtitle_url': self.subtitle_url
        }

class SubtitleFormat:
    """字幕格式常量"""
    JSON = 'json'
    XML = 'xml'
    SRT = 'srt'
    VTT = 'vtt'
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """获取支持的字幕格式"""
        return [cls.JSON, cls.XML, cls.SRT, cls.VTT]
    
    @classmethod
    def is_supported(cls, format_name: str) -> bool:
        """检查格式是否支持"""
        return format_name.lower() in cls.get_supported_formats()

class ExtractionError(Exception):
    """提取异常基类"""
    pass

class VideoNotFoundError(ExtractionError):
    """视频未找到异常"""
    pass

class SubtitleNotFoundError(ExtractionError):
    """字幕未找到异常"""
    pass

class NetworkError(ExtractionError):
    """网络异常"""
    pass

class ParseError(ExtractionError):
    """解析异常"""
    pass

class RateLimitError(ExtractionError):
    """请求频率限制异常"""
    pass