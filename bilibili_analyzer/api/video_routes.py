"""
视频处理API路由
"""

import json
from flask import request, current_app
from . import bp
from .utils import APIResponse, APIValidator, require_rate_limit
from bilibili_analyzer.models import db, Video, Subtitle
from bilibili_analyzer.extractors.video_extractor import VideoExtractor, VideoNotFoundError, SubtitleNotFoundError

# 初始化视频提取器
video_extractor = VideoExtractor()

@bp.route('/v1/video/extract', methods=['POST'])
@require_rate_limit
def extract_video_info():
    """提取视频信息"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json(['bvid'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        bvid = data['bvid']
        
        # 提取视频信息
        video_info = video_extractor.extract_video_info(bvid)
        
        # 保存到数据库
        video = Video.query.filter_by(bvid=bvid).first()
        if not video:
            video = Video(
                bvid=bvid,
                title=video_info.title,
                author=video_info.author,
                duration=video_info.duration,
                publish_date=video_info.publish_date,
                thumbnail_url=video_info.thumbnail_url
            )
            db.session.add(video)
        
        # 更新视频信息
        video.title = video_info.title
        video.author = video_info.author
        video.duration = video_info.duration
        video.publish_date = video_info.publish_date
        video.thumbnail_url = video_info.thumbnail_url
        
        db.session.commit()
        
        # 格式化响应
        response_data = {
            'video_info': {
                'bvid': video_info.bvid,
                'title': video_info.title,
                'author': video_info.author,
                'duration': video_info.duration,
                'publish_date': video_info.publish_date.isoformat() if video_info.publish_date else None,
                'thumbnail_url': video_info.thumbnail_url,
                'description': video_info.description,
                'view_count': video_info.view_count,
                'like_count': video_info.like_count,
                'coin_count': video_info.coin_count,
                'favorite_count': video_info.favorite_count,
                'share_count': video_info.share_count
            },
            'subtitle_available': video_extractor.check_subtitle_available(bvid),
            'db_id': video.id
        }
        
        return APIResponse.success(response_data, "Video information extracted successfully")
        
    except VideoNotFoundError as e:
        return APIResponse.error(f"Video not found: {str(e)}", 404, "VIDEO_NOT_FOUND")
    except Exception as e:
        current_app.logger.error(f"Error extracting video info: {e}")
        return APIResponse.error(f"Failed to extract video information: {str(e)}", 500)

@bp.route('/v1/subtitle/download', methods=['POST'])
@require_rate_limit
def download_subtitle():
    """下载字幕"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json(['bvid'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        bvid = data['bvid']
        language = data.get('language', 'zh-CN')
        
        # 检查视频是否存在
        video = Video.query.filter_by(bvid=bvid).first()
        if not video:
            return APIResponse.error("Video not found in database", 404, "VIDEO_NOT_FOUND")
        
        # 下载字幕
        subtitle = video_extractor.download_subtitle(bvid, language)
        
        # 保存到数据库
        db_subtitle = Subtitle.query.filter_by(
            video_id=video.id,
            language=language
        ).first()
        
        if not db_subtitle:
            db_subtitle = Subtitle(
                video_id=video.id,
                language=subtitle.language,
                format=subtitle.format,
                content=subtitle.content
            )
            db.session.add(db_subtitle)
        else:
            # 更新字幕内容
            db_subtitle.content = subtitle.content
            db_subtitle.format = subtitle.format
        
        db.session.commit()
        
        # 格式化响应
        response_data = {
            'subtitle': {
                'id': db_subtitle.id,
                'video_id': video.id,
                'bvid': bvid,
                'language': subtitle.language,
                'format': subtitle.format,
                'line_count': len(subtitle.lines),
                'created_at': db_subtitle.created_at.isoformat() if db_subtitle.created_at else None
            },
            'subtitle_lines': [
                {
                    'index': line.index,
                    'start_time': line.start_time,
                    'end_time': line.end_time,
                    'text': line.text
                }
                for line in subtitle.lines
            ]
        }
        
        return APIResponse.success(response_data, "Subtitle downloaded successfully")
        
    except SubtitleNotFoundError as e:
        return APIResponse.error(f"Subtitle not found: {str(e)}", 404, "SUBTITLE_NOT_FOUND")
    except VideoNotFoundError as e:
        return APIResponse.error(f"Video not found: {str(e)}", 404, "VIDEO_NOT_FOUND")
    except Exception as e:
        current_app.logger.error(f"Error downloading subtitle: {e}")
        return APIResponse.error(f"Failed to download subtitle: {str(e)}", 500)

@bp.route('/v1/video/<bvid>', methods=['GET'])
@require_rate_limit
def get_video_info(bvid):
    """获取视频信息"""
    try:
        # 从数据库获取视频信息
        video = Video.query.filter_by(bvid=bvid).first()
        if not video:
            return APIResponse.error("Video not found in database", 404, "VIDEO_NOT_FOUND")
        
        # 获取最新字幕
        latest_subtitle = video.get_latest_subtitle()
        subtitle_info = None
        
        if latest_subtitle:
            subtitle_info = {
                'id': latest_subtitle.id,
                'language': latest_subtitle.language,
                'format': latest_subtitle.format,
                'created_at': latest_subtitle.created_at.isoformat() if latest_subtitle.created_at else None
            }
        
        # 获取最新分析结果
        latest_analysis = video.get_latest_analysis()
        analysis_info = None
        
        if latest_analysis:
            analysis_info = {
                'id': latest_analysis.id,
                'summary': latest_analysis.summary,
                'model_used': latest_analysis.model_used,
                'analysis_time': latest_analysis.analysis_time,
                'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else None
            }
        
        response_data = {
            'video': video.to_dict(),
            'subtitle': subtitle_info,
            'analysis': analysis_info
        }
        
        return APIResponse.success(response_data, "Video information retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting video info: {e}")
        return APIResponse.error(f"Failed to get video information: {str(e)}", 500)

@bp.route('/v1/video/<bvid>/subtitle', methods=['GET'])
@require_rate_limit
def get_video_subtitle(bvid):
    """获取视频字幕"""
    try:
        # 验证查询参数
        is_valid, error_msg, params = APIValidator.validate_query_params()
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        language = params.get('language', 'zh-CN')
        
        # 检查视频是否存在
        video = Video.query.filter_by(bvid=bvid).first()
        if not video:
            return APIResponse.error("Video not found in database", 404, "VIDEO_NOT_FOUND")
        
        # 获取指定语言的字幕
        subtitle = Subtitle.query.filter_by(
            video_id=video.id,
            language=language
        ).first()
        
        if not subtitle:
            return APIResponse.error(f"Subtitle not found for language: {language}", 404, "SUBTITLE_NOT_FOUND")
        
        # 解析字幕内容
        subtitle_lines = subtitle.get_content_lines()
        
        response_data = {
            'subtitle': {
                'id': subtitle.id,
                'video_id': video.id,
                'bvid': bvid,
                'language': subtitle.language,
                'format': subtitle.format,
                'created_at': subtitle.created_at.isoformat() if subtitle.created_at else None
            },
            'lines': subtitle_lines
        }
        
        return APIResponse.success(response_data, "Subtitle retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting video subtitle: {e}")
        return APIResponse.error(f"Failed to get video subtitle: {str(e)}", 500)

@bp.route('/v1/videos', methods=['GET'])
@require_rate_limit
def list_videos():
    """获取视频列表"""
    try:
        # 获取分页参数
        page, per_page = APIValidator.validate_pagination_params()
        
        # 获取查询参数
        search = request.args.get('search', '')
        has_subtitle = request.args.get('has_subtitle', '').lower() == 'true'
        has_analysis = request.args.get('has_analysis', '').lower() == 'true'
        
        # 构建查询
        query = Video.query
        
        # 搜索过滤
        if search:
            query = query.filter(
                Video.title.contains(search) | Video.author.contains(search)
            )
        
        # 字幕过滤
        if has_subtitle:
            query = query.join(Video.subtitles).distinct()
        
        # 分析结果过滤
        if has_analysis:
            query = query.join(Video.analyses).distinct()
        
        # 分页查询
        pagination = query.order_by(Video.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 格式化响应
        videos_data = []
        for video in pagination.items:
            video_data = video.to_dict()
            
            # 添加字幕信息
            latest_subtitle = video.get_latest_subtitle()
            if latest_subtitle:
                video_data['subtitle'] = {
                    'id': latest_subtitle.id,
                    'language': latest_subtitle.language,
                    'created_at': latest_subtitle.created_at.isoformat() if latest_subtitle.created_at else None
                }
            
            # 添加分析信息
            latest_analysis = video.get_latest_analysis()
            if latest_analysis:
                video_data['analysis'] = {
                    'id': latest_analysis.id,
                    'summary': latest_analysis.summary,
                    'model_used': latest_analysis.model_used,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else None
                }
            
            videos_data.append(video_data)
        
        return APIResponse.paginated(
            videos_data,
            pagination.total,
            page,
            per_page,
            "Videos retrieved successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Error listing videos: {e}")
        return APIResponse.error(f"Failed to list videos: {str(e)}", 500)