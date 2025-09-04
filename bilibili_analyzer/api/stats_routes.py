"""
统计和监控API路由
"""

import json
from datetime import datetime, timedelta
from flask import request, current_app
from . import bp
from .utils import APIResponse, APIValidator, require_rate_limit
from bilibili_analyzer.models import db, Video, Subtitle, Analysis, KnowledgeEntry, Tag, knowledge_tags
from sqlalchemy import func, and_, or_

@bp.route('/v1/stats', methods=['GET'])
@require_rate_limit
def get_system_stats():
    """获取系统统计信息"""
    try:
        # 基础统计
        total_videos = Video.query.count()
        total_subtitles = Subtitle.query.count()
        total_analyses = Analysis.query.count()
        total_knowledge_entries = KnowledgeEntry.query.count()
        total_tags = Tag.query.count()
        
        # 视频统计
        videos_with_subtitles = Video.query.join(Video.subtitles).distinct().count()
        videos_with_analyses = Video.query.join(Video.analyses).distinct().count()
        
        # 分析统计
        avg_analysis_time = db.session.query(func.avg(Analysis.analysis_time)).scalar() or 0
        total_analysis_time = db.session.query(func.sum(Analysis.analysis_time)).scalar() or 0
        
        # 按模型统计
        model_stats = db.session.query(
            Analysis.model_used,
            func.count(Analysis.id).label('count'),
            func.avg(Analysis.analysis_time).label('avg_time')
        ).group_by(Analysis.model_used).all()
        
        # 知识库统计
        knowledge_type_stats = db.session.query(
            KnowledgeEntry.knowledge_type,
            func.count(KnowledgeEntry.id).label('count')
        ).group_by(KnowledgeEntry.knowledge_type).all()
        
        importance_stats = db.session.query(
            KnowledgeEntry.importance,
            func.count(KnowledgeEntry.id).label('count')
        ).group_by(KnowledgeEntry.importance).all()
        
        # 标签统计
        tags_with_usage = Tag.query.outerjoin(Tag.knowledge_entries).group_by(Tag.id).having(
            func.count(knowledge_tags.c.knowledge_entry_id) > 0
        ).count()
        
        # 最近活动统计
        recent_videos = Video.query.order_by(Video.created_at.desc()).limit(10).all()
        recent_analyses = Analysis.query.order_by(Analysis.created_at.desc()).limit(10).all()
        recent_knowledge = KnowledgeEntry.query.order_by(KnowledgeEntry.created_at.desc()).limit(10).all()
        
        # 时间范围统计
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        videos_last_24h = Video.query.filter(Video.created_at >= last_24h).count()
        videos_last_7d = Video.query.filter(Video.created_at >= last_7d).count()
        videos_last_30d = Video.query.filter(Video.created_at >= last_30d).count()
        
        analyses_last_24h = Analysis.query.filter(Analysis.created_at >= last_24h).count()
        analyses_last_7d = Analysis.query.filter(Analysis.created_at >= last_7d).count()
        analyses_last_30d = Analysis.query.filter(Analysis.created_at >= last_30d).count()
        
        # 构建响应
        stats = {
            'overview': {
                'total_videos': total_videos,
                'total_subtitles': total_subtitles,
                'total_analyses': total_analyses,
                'total_knowledge_entries': total_knowledge_entries,
                'total_tags': total_tags,
                'videos_with_subtitles': videos_with_subtitles,
                'videos_with_analyses': videos_with_analyses,
                'subtitle_coverage': round(videos_with_subtitles / total_videos * 100, 2) if total_videos > 0 else 0,
                'analysis_coverage': round(videos_with_analyses / total_videos * 100, 2) if total_videos > 0 else 0
            },
            'analysis_stats': {
                'avg_analysis_time': round(avg_analysis_time, 2),
                'total_analysis_time': round(total_analysis_time, 2),
                'model_distribution': [
                    {
                        'model': stat.model_used or 'Unknown',
                        'count': stat.count,
                        'avg_time': round(stat.avg_time, 2)
                    }
                    for stat in model_stats
                ]
            },
            'knowledge_stats': {
                'type_distribution': [
                    {
                        'type': stat.knowledge_type,
                        'count': stat.count
                    }
                    for stat in knowledge_type_stats
                ],
                'importance_distribution': [
                    {
                        'importance': stat.importance,
                        'count': stat.count
                    }
                    for stat in importance_stats
                ],
                'avg_entries_per_analysis': round(total_knowledge_entries / total_analyses, 2) if total_analyses > 0 else 0
            },
            'tag_stats': {
                'total_tags': total_tags,
                'tags_with_usage': tags_with_usage,
                'unused_tags': total_tags - tags_with_usage
            },
            'activity_stats': {
                'videos': {
                    'last_24h': videos_last_24h,
                    'last_7d': videos_last_7d,
                    'last_30d': videos_last_30d
                },
                'analyses': {
                    'last_24h': analyses_last_24h,
                    'last_7d': analyses_last_7d,
                    'last_30d': analyses_last_30d
                }
            },
            'recent_activity': {
                'videos': [
                    {
                        'id': video.id,
                        'bvid': video.bvid,
                        'title': video.title,
                        'created_at': video.created_at.isoformat() if video.created_at else None
                    }
                    for video in recent_videos
                ],
                'analyses': [
                    {
                        'id': analysis.id,
                        'video': {
                            'id': analysis.video.id,
                            'bvid': analysis.video.bvid,
                            'title': analysis.video.title
                        } if analysis.video else None,
                        'model_used': analysis.model_used,
                        'analysis_time': analysis.analysis_time,
                        'created_at': analysis.created_at.isoformat() if analysis.created_at else None
                    }
                    for analysis in recent_analyses
                ],
                'knowledge_entries': [
                    {
                        'id': entry.id,
                        'title': entry.title,
                        'knowledge_type': entry.knowledge_type,
                        'importance': entry.importance,
                        'created_at': entry.created_at.isoformat() if entry.created_at else None
                    }
                    for entry in recent_knowledge
                ]
            }
        }
        
        return APIResponse.success(stats, "System statistics retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting system stats: {e}")
        return APIResponse.error(f"Failed to get system stats: {str(e)}", 500)

@bp.route('/v1/stats/analysis', methods=['GET'])
@require_rate_limit
def get_analysis_stats():
    """获取分析统计信息"""
    try:
        # 获取查询参数
        days = request.args.get('days', 30, type=int)
        days = min(days, 365)  # 限制最大查询范围
        
        # 时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 基础统计
        total_analyses = Analysis.query.filter(
            Analysis.created_at >= start_date
        ).count()
        
        avg_analysis_time = db.session.query(func.avg(Analysis.analysis_time)).filter(
            Analysis.created_at >= start_date
        ).scalar() or 0
        
        # 按模型统计
        model_stats = db.session.query(
            Analysis.model_used,
            func.count(Analysis.id).label('count'),
            func.avg(Analysis.analysis_time).label('avg_time'),
            func.sum(Analysis.analysis_time).label('total_time')
        ).filter(
            Analysis.created_at >= start_date
        ).group_by(Analysis.model_used).all()
        
        # 按日期统计
        daily_stats = db.session.query(
            func.date(Analysis.created_at).label('date'),
            func.count(Analysis.id).label('count'),
            func.avg(Analysis.analysis_time).label('avg_time')
        ).filter(
            Analysis.created_at >= start_date
        ).group_by(func.date(Analysis.created_at)).order_by(func.date(Analysis.created_at)).all()
        
        # 按小时统计（最近7天）
        hourly_stats = []
        if days <= 7:
            hourly_stats = db.session.query(
                func.strftime('%H', Analysis.created_at).label('hour'),
                func.count(Analysis.id).label('count')
            ).filter(
                Analysis.created_at >= start_date
            ).group_by(func.strftime('%H', Analysis.created_at)).all()
        
        # 构建响应
        stats = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'summary': {
                'total_analyses': total_analyses,
                'avg_analysis_time': round(avg_analysis_time, 2),
                'analyses_per_day': round(total_analyses / days, 2)
            },
            'model_stats': [
                {
                    'model': stat.model_used or 'Unknown',
                    'count': stat.count,
                    'avg_time': round(stat.avg_time, 2),
                    'total_time': round(stat.total_time, 2),
                    'percentage': round(stat.count / total_analyses * 100, 2) if total_analyses > 0 else 0
                }
                for stat in model_stats
            ],
            'daily_stats': [
                {
                    'date': stat.date.isoformat(),
                    'count': stat.count,
                    'avg_time': round(stat.avg_time, 2)
                }
                for stat in daily_stats
            ],
            'hourly_stats': [
                {
                    'hour': int(stat.hour),
                    'count': stat.count
                }
                for stat in hourly_stats
            ]
        }
        
        return APIResponse.success(stats, "Analysis statistics retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting analysis stats: {e}")
        return APIResponse.error(f"Failed to get analysis stats: {str(e)}", 500)

@bp.route('/v1/stats/knowledge', methods=['GET'])
@require_rate_limit
def get_knowledge_stats_endpoint():
    """获取知识库统计信息"""
    try:
        # 基础统计
        total_entries = KnowledgeEntry.query.count()
        total_tags = Tag.query.count()
        
        # 按类型统计
        type_stats = db.session.query(
            KnowledgeEntry.knowledge_type,
            func.count(KnowledgeEntry.id).label('count')
        ).group_by(KnowledgeEntry.knowledge_type).all()
        
        # 按重要性统计
        importance_stats = db.session.query(
            KnowledgeEntry.importance,
            func.count(KnowledgeEntry.id).label('count')
        ).group_by(KnowledgeEntry.importance).all()
        
        # 按创建时间统计
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        entries_last_24h = KnowledgeEntry.query.filter(KnowledgeEntry.created_at >= last_24h).count()
        entries_last_7d = KnowledgeEntry.query.filter(KnowledgeEntry.created_at >= last_7d).count()
        entries_last_30d = KnowledgeEntry.query.filter(KnowledgeEntry.created_at >= last_30d).count()
        
        # 标签使用统计
        tag_usage_stats = db.session.query(
            Tag.name,
            func.count(knowledge_tags.c.knowledge_entry_id).label('usage_count')
        ).join(knowledge_tags).group_by(Tag.id).order_by(
            func.count(knowledge_tags.c.knowledge_entry_id).desc()
        ).limit(20).all()
        
        # 热门知识条目（按重要性）
        top_entries = KnowledgeEntry.query.order_by(
            KnowledgeEntry.importance.desc(),
            KnowledgeEntry.created_at.desc()
        ).limit(10).all()
        
        # 构建响应
        stats = {
            'overview': {
                'total_entries': total_entries,
                'total_tags': total_tags,
                'entries_last_24h': entries_last_24h,
                'entries_last_7d': entries_last_7d,
                'entries_last_30d': entries_last_30d
            },
            'type_distribution': [
                {
                    'type': stat.knowledge_type,
                    'count': stat.count,
                    'percentage': round(stat.count / total_entries * 100, 2) if total_entries > 0 else 0
                }
                for stat in type_stats
            ],
            'importance_distribution': [
                {
                    'importance': stat.importance,
                    'count': stat.count,
                    'percentage': round(stat.count / total_entries * 100, 2) if total_entries > 0 else 0
                }
                for stat in importance_stats
            ],
            'popular_tags': [
                {
                    'name': stat.name,
                    'usage_count': stat.usage_count
                }
                for stat in tag_usage_stats
            ],
            'top_entries': [
                {
                    'id': entry.id,
                    'title': entry.title,
                    'knowledge_type': entry.knowledge_type,
                    'importance': entry.importance,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None
                }
                for entry in top_entries
            ]
        }
        
        return APIResponse.success(stats, "Knowledge base statistics retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting knowledge stats: {e}")
        return APIResponse.error(f"Failed to get knowledge stats: {str(e)}", 500)

@bp.route('/v1/stats/performance', methods=['GET'])
@require_rate_limit
def get_performance_stats():
    """获取性能统计信息"""
    try:
        # 分析性能统计
        performance_stats = db.session.query(
            func.avg(Analysis.analysis_time).label('avg_time'),
            func.min(Analysis.analysis_time).label('min_time'),
            func.max(Analysis.analysis_time).label('max_time'),
            func.count(Analysis.id).label('total_count')
        ).filter(
            Analysis.analysis_time > 0
        ).first()
        
        # 按模型性能统计
        model_performance = db.session.query(
            Analysis.model_used,
            func.avg(Analysis.analysis_time).label('avg_time'),
            func.min(Analysis.analysis_time).label('min_time'),
            func.max(Analysis.analysis_time).label('max_time'),
            func.count(Analysis.id).label('count')
        ).filter(
            Analysis.analysis_time > 0
        ).group_by(Analysis.model_used).all()
        
        # 性能分布
        fast_analyses = Analysis.query.filter(Analysis.analysis_time < 10).count()
        medium_analyses = Analysis.query.filter(
            and_(Analysis.analysis_time >= 10, Analysis.analysis_time < 30)
        ).count()
        slow_analyses = Analysis.query.filter(Analysis.analysis_time >= 30).count()
        
        # 构建响应
        stats = {
            'overall_performance': {
                'avg_time': round(performance_stats.avg_time, 2) if performance_stats.avg_time else 0,
                'min_time': round(performance_stats.min_time, 2) if performance_stats.min_time else 0,
                'max_time': round(performance_stats.max_time, 2) if performance_stats.max_time else 0,
                'total_count': performance_stats.total_count or 0
            },
            'model_performance': [
                {
                    'model': stat.model_used or 'Unknown',
                    'avg_time': round(stat.avg_time, 2) if stat.avg_time else 0,
                    'min_time': round(stat.min_time, 2) if stat.min_time else 0,
                    'max_time': round(stat.max_time, 2) if stat.max_time else 0,
                    'count': stat.count
                }
                for stat in model_performance
            ],
            'performance_distribution': {
                'fast_analyses': fast_analyses,
                'medium_analyses': medium_analyses,
                'slow_analyses': slow_analyses,
                'total_analyses': fast_analyses + medium_analyses + slow_analyses
            }
        }
        
        return APIResponse.success(stats, "Performance statistics retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting performance stats: {e}")
        return APIResponse.error(f"Failed to get performance stats: {str(e)}", 500)

@bp.route('/v1/health/detailed', methods=['GET'])
@require_rate_limit
def get_detailed_health():
    """获取详细健康状态"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # 数据库健康检查
        try:
            db.session.execute('SELECT 1')
            health_status['components']['database'] = {
                'status': 'healthy',
                'message': 'Database connection is working'
            }
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            health_status['status'] = 'degraded'
        
        # 检查数据库表
        try:
            table_counts = {
                'videos': Video.query.count(),
                'subtitles': Subtitle.query.count(),
                'analyses': Analysis.query.count(),
                'knowledge_entries': KnowledgeEntry.query.count(),
                'tags': Tag.query.count()
            }
            health_status['components']['database_tables'] = {
                'status': 'healthy',
                'table_counts': table_counts
            }
        except Exception as e:
            health_status['components']['database_tables'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            health_status['status'] = 'degraded'
        
        # 检查最近的系统活动
        try:
            now = datetime.utcnow()
            recent_activity = now - timedelta(hours=1)
            
            recent_analyses = Analysis.query.filter(Analysis.created_at >= recent_activity).count()
            recent_entries = KnowledgeEntry.query.filter(KnowledgeEntry.created_at >= recent_activity).count()
            
            health_status['components']['activity'] = {
                'status': 'healthy',
                'recent_analyses': recent_analyses,
                'recent_knowledge_entries': recent_entries
            }
        except Exception as e:
            health_status['components']['activity'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
            health_status['status'] = 'degraded'
        
        # 检查错误率（假设有错误日志）
        try:
            # 这里可以添加错误日志检查逻辑
            error_rate = 0.0  # 从日志系统获取
            health_status['components']['error_rate'] = {
                'status': 'healthy',
                'error_rate': error_rate,
                'threshold': 0.05  # 5%错误率阈值
            }
        except Exception as e:
            health_status['components']['error_rate'] = {
                'status': 'unknown',
                'message': str(e)
            }
        
        return APIResponse.success(health_status, "Detailed health status retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting detailed health status: {e}")
        return APIResponse.error(f"Failed to get detailed health status: {str(e)}", 500)