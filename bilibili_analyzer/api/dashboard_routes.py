"""
仪表板和活动API路由
"""

import json
from datetime import datetime, timedelta
from flask import request, current_app
from . import bp
from .utils import APIResponse, APIValidator, require_rate_limit
from bilibili_analyzer.models import db, Video, Analysis, KnowledgeEntry, Tag
from sqlalchemy import func, and_, or_

@bp.route('/v1/activity/recent', methods=['GET'])
@require_rate_limit
def get_recent_activity():
    """获取最近活动"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # 限制最大数量
        
        # 获取最近的分析活动
        recent_analyses = db.session.query(
            Analysis.id,
            Analysis.created_at,
            Analysis.model_used,
            Video.title.label('video_title'),
            Video.bvid
        ).join(Video).order_by(Analysis.created_at.desc()).limit(limit).all()
        
        # 获取最近的知识条目活动
        recent_entries = db.session.query(
            KnowledgeEntry.id,
            KnowledgeEntry.created_at,
            KnowledgeEntry.title,
            KnowledgeEntry.knowledge_type,
            Video.title.label('video_title')
        ).join(Analysis).join(Video).order_by(KnowledgeEntry.created_at.desc()).limit(limit).all()
        
        # 合并活动记录
        activities = []
        
        # 添加分析活动
        for analysis in recent_analyses:
            activities.append({
                'id': f'analysis_{analysis.id}',
                'type': 'analysis',
                'title': f'分析了视频: {analysis.video_title}',
                'timestamp': analysis.created_at.isoformat(),
                'data': {
                    'analysis_id': analysis.id,
                    'video_title': analysis.video_title,
                    'bvid': analysis.bvid,
                    'model_used': analysis.model_used
                }
            })
        
        # 添加知识条目活动
        for entry in recent_entries:
            activities.append({
                'id': f'knowledge_{entry.id}',
                'type': 'knowledge',
                'title': f'创建了知识条目: {entry.title}',
                'timestamp': entry.created_at.isoformat(),
                'data': {
                    'entry_id': entry.id,
                    'entry_title': entry.title,
                    'knowledge_type': entry.knowledge_type,
                    'video_title': entry.video_title
                }
            })
        
        # 按时间排序
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 限制数量
        activities = activities[:limit]
        
        return APIResponse.success(activities, "Recent activity retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting recent activity: {e}")
        return APIResponse.error(f"Failed to get recent activity: {str(e)}", 500)

@bp.route('/v1/videos/top', methods=['GET'])
@require_rate_limit
def get_top_videos():
    """获取热门视频"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 5, type=int)
        limit = min(limit, 20)  # 限制最大数量
        
        # 按观看次数排序
        top_videos = Video.query.order_by(
            Video.view_count.desc().nullslast()
        ).limit(limit).all()
        
        # 格式化响应
        videos_data = []
        for video in top_videos:
            # 获取分析次数
            analysis_count = Analysis.query.filter_by(video_id=video.id).count()
            
            videos_data.append({
                'id': video.id,
                'bvid': video.bvid,
                'title': video.title,
                'author': video.author,
                'view_count': video.view_count or 0,
                'like_count': video.like_count or 0,
                'analysis_count': analysis_count,
                'cover_url': video.cover_url,
                'created_at': video.created_at.isoformat() if video.created_at else None
            })
        
        return APIResponse.success(videos_data, "Top videos retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting top videos: {e}")
        return APIResponse.error(f"Failed to get top videos: {str(e)}", 500)

@bp.route('/v1/tags/top', methods=['GET'])
@require_rate_limit
def get_top_tags():
    """获取热门标签"""
    try:
        # 获取查询参数
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # 限制最大数量
        
        # 获取标签使用统计
        from bilibili_analyzer.models import knowledge_tags
        
        tag_stats = db.session.query(
            Tag.id,
            Tag.name,
            func.count(knowledge_tags.c.knowledge_entry_id).label('usage_count')
        ).join(knowledge_tags).group_by(Tag.id).order_by(
            func.count(knowledge_tags.c.knowledge_entry_id).desc()
        ).limit(limit).all()
        
        # 格式化响应
        tags_data = []
        for tag in tag_stats:
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'count': tag.usage_count
            })
        
        return APIResponse.success(tags_data, "Top tags retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting top tags: {e}")
        return APIResponse.error(f"Failed to get top tags: {str(e)}", 500)

@bp.route('/v1/stats/analysis-trend', methods=['GET'])
@require_rate_limit
def get_analysis_trend():
    """获取分析趋势"""
    try:
        # 获取查询参数
        days = request.args.get('days', 7, type=int)
        days = min(days, 30)  # 限制最大查询范围
        
        # 时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 按日期统计分析次数
        daily_stats = db.session.query(
            func.date(Analysis.created_at).label('date'),
            func.count(Analysis.id).label('count')
        ).filter(
            Analysis.created_at >= start_date
        ).group_by(func.date(Analysis.created_at)).order_by(func.date(Analysis.created_at)).all()
        
        # 生成完整的日期序列
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date.date())
            current_date += timedelta(days=1)
        
        # 构建响应数据
        labels = [date.strftime('%m-%d') for date in date_range]
        values = []
        
        # 填充数据
        stats_dict = {stat.date: stat.count for stat in daily_stats}
        for date in date_range:
            values.append(stats_dict.get(date, 0))
        
        trend_data = {
            'labels': labels,
            'values': values,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        }
        
        return APIResponse.success(trend_data, "Analysis trend retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting analysis trend: {e}")
        return APIResponse.error(f"Failed to get analysis trend: {str(e)}", 500)

@bp.route('/v1/stats/knowledge-types', methods=['GET'])
@require_rate_limit
def get_knowledge_type_stats():
    """获取知识类型统计"""
    try:
        # 按类型统计知识条目
        type_stats = db.session.query(
            KnowledgeEntry.knowledge_type,
            func.count(KnowledgeEntry.id).label('count')
        ).group_by(KnowledgeEntry.knowledge_type).all()
        
        # 格式化响应
        labels = []
        values = []
        
        type_labels = {
            'concept': '概念',
            'definition': '定义',
            'example': '示例',
            'technique': '技巧'
        }
        
        for stat in type_stats:
            labels.append(type_labels.get(stat.knowledge_type, stat.knowledge_type))
            values.append(stat.count)
        
        type_data = {
            'labels': labels,
            'values': values
        }
        
        return APIResponse.success(type_data, "Knowledge type statistics retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting knowledge type stats: {e}")
        return APIResponse.error(f"Failed to get knowledge type stats: {str(e)}", 500)

@bp.route('/v1/system/info', methods=['GET'])
@require_rate_limit
def get_system_info():
    """获取系统信息"""
    try:
        import platform
        import psutil
        
        # 系统信息
        system_info = {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
        
        # 内存信息
        memory = psutil.virtual_memory()
        system_info['memory'] = {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        }
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        system_info['disk'] = {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        }
        
        # 运行时间（假设应用启动时间）
        uptime = datetime.utcnow() - current_app.start_time if hasattr(current_app, 'start_time') else timedelta(hours=1)
        system_info['uptime'] = uptime.total_seconds()
        
        # 版本信息
        system_info['version'] = {
            'app_version': '1.0.0',
            'api_version': 'v1'
        }
        
        return APIResponse.success(system_info, "System information retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting system info: {e}")
        return APIResponse.error(f"Failed to get system info: {str(e)}", 500)