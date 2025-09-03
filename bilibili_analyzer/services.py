"""
Bilibili视频分析系统 - 数据库集成服务
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from bilibili_analyzer.models import Video, Subtitle, db
from bilibili_analyzer.extractors import (
    VideoExtractor, VideoInfo, Subtitle as ExtractorSubtitle, 
    SubtitleLine, ExtractionError
)
from bilibili_analyzer.utils import close_request_handler

class DatabaseService:
    """数据库服务类，用于集成提取器和数据库模型"""
    
    def __init__(self):
        self.extractor = VideoExtractor()
    
    def save_video_info(self, video_info: VideoInfo) -> Video:
        """
        保存视频信息到数据库
        
        Args:
            video_info: 视频信息对象
            
        Returns:
            数据库视频对象
        """
        # 检查是否已存在
        existing_video = Video.query.filter_by(bvid=video_info.bvid).first()
        
        if existing_video:
            # 更新现有记录
            existing_video.title = video_info.title
            existing_video.author = video_info.author
            existing_video.duration = video_info.duration
            existing_video.publish_date = video_info.publish_date
            existing_video.thumbnail_url = video_info.thumbnail_url
            existing_video.updated_at = datetime.utcnow()
            db.session.commit()
            return existing_video
        else:
            # 创建新记录
            video = Video(
                bvid=video_info.bvid,
                title=video_info.title,
                author=video_info.author,
                duration=video_info.duration,
                publish_date=video_info.publish_date,
                thumbnail_url=video_info.thumbnail_url
            )
            db.session.add(video)
            db.session.commit()
            return video
    
    def save_subtitle(self, video: Video, subtitle: ExtractorSubtitle) -> Subtitle:
        """
        保存字幕到数据库
        
        Args:
            video: 视频对象
            subtitle: 字幕对象
            
        Returns:
            数据库字幕对象
        """
        # 检查是否已存在相同语言的字幕
        existing_subtitle = Subtitle.query.filter_by(
            video_id=video.id,
            language=subtitle.language
        ).first()
        
        if existing_subtitle:
            # 更新现有记录
            existing_subtitle.content = subtitle.content
            existing_subtitle.format = subtitle.format
            existing_subtitle.updated_at = datetime.utcnow()
            db.session.commit()
            return existing_subtitle
        else:
            # 创建新记录
            db_subtitle = Subtitle(
                video_id=video.id,
                language=subtitle.language,
                format=subtitle.format,
                content=subtitle.content,
                file_path=subtitle.file_path
            )
            db.session.add(db_subtitle)
            db.session.commit()
            return db_subtitle
    
    def extract_and_save_video(self, bvid: str, language: str = 'zh-CN') -> Dict[str, Any]:
        """
        提取并保存视频信息
        
        Args:
            bvid: B站视频ID
            language: 字幕语言
            
        Returns:
            操作结果字典
        """
        result = {
            'success': False,
            'video': None,
            'subtitle': None,
            'subtitle_available': False,
            'error': None
        }
        
        try:
            # 提取视频信息
            video_info = self.extractor.extract_video_info(bvid)
            
            # 保存视频信息
            video = self.save_video_info(video_info)
            result['video'] = video
            
            # 检查字幕
            subtitle_available = self.extractor.check_subtitle_available(bvid)
            result['subtitle_available'] = subtitle_available
            
            if subtitle_available:
                try:
                    # 下载字幕
                    subtitle = self.extractor.download_subtitle(bvid, language)
                    
                    # 保存字幕
                    db_subtitle = self.save_subtitle(video, subtitle)
                    result['subtitle'] = db_subtitle
                    
                except Exception as e:
                    result['subtitle_available'] = False
                    result['error'] = f"字幕保存失败: {str(e)}"
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_video_by_bvid(self, bvid: str) -> Optional[Video]:
        """
        根据BV号获取视频
        
        Args:
            bvid: B站视频ID
            
        Returns:
            视频对象或None
        """
        return Video.query.filter_by(bvid=bvid).first()
    
    def get_subtitle_by_video_id(self, video_id: int, language: str = 'zh-CN') -> Optional[Subtitle]:
        """
        根据视频ID获取字幕
        
        Args:
            video_id: 视频ID
            language: 语言代码
            
        Returns:
            字幕对象或None
        """
        return Subtitle.query.filter_by(
            video_id=video_id,
            language=language
        ).first()
    
    def get_or_extract_video(self, bvid: str, language: str = 'zh-CN', 
                            force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取或提取视频信息
        
        Args:
            bvid: B站视频ID
            language: 字幕语言
            force_refresh: 是否强制刷新
            
        Returns:
            操作结果字典
        """
        result = {
            'success': False,
            'video': None,
            'subtitle': None,
            'subtitle_available': False,
            'from_cache': False,
            'error': None
        }
        
        try:
            # 检查数据库中是否已有记录
            if not force_refresh:
                video = self.get_video_by_bvid(bvid)
                if video:
                    subtitle = self.get_subtitle_by_video_id(video.id, language)
                    result['video'] = video
                    result['subtitle'] = subtitle
                    result['subtitle_available'] = subtitle is not None
                    result['from_cache'] = True
                    result['success'] = True
                    return result
            
            # 没有记录或强制刷新，进行提取
            return self.extract_and_save_video(bvid, language)
            
        except Exception as e:
            result['error'] = str(e)
            return result
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """
        清理旧数据
        
        Args:
            days: 保留天数
            
        Returns:
            删除的记录数
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 删除旧的视频记录（级联删除相关字幕和分析）
        deleted_count = Video.query.filter(
            Video.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        return deleted_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_videos': Video.query.count(),
            'total_subtitles': Subtitle.query.count(),
            'videos_with_subtitles': Video.query.join(Video.subtitles).distinct().count(),
            'recent_videos': Video.query.filter(
                Video.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()
        }
    
    def __del__(self):
        """析构函数，关闭请求处理器"""
        try:
            close_request_handler()
        except:
            pass