"""
内容分析API路由
"""

import json
import asyncio
from datetime import datetime
from flask import request, current_app
from . import bp
from .utils import APIResponse, APIValidator, require_rate_limit
from bilibili_analyzer.models import db, Video, Subtitle, Analysis
from bilibili_analyzer.analyzers.content_analyzer import ContentAnalyzer, AnalysisConfig, AnalysisResult
from bilibili_analyzer.services.llm import LLMServiceManager

# 全局分析器实例（在生产环境中应该使用依赖注入）
analyzer = None

def get_analyzer():
    """获取分析器实例"""
    global analyzer
    if analyzer is None:
        # 初始化LLM服务管理器
        llm_manager = LLMServiceManager()
        # 初始化分析器
        analyzer = ContentAnalyzer(llm_manager, AnalysisConfig())
    return analyzer

@bp.route('/v1/analyze', methods=['POST'])
@require_rate_limit
def analyze_content():
    """分析内容"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json(['bvid'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        bvid = data['bvid']
        language = data.get('language', 'zh-CN')
        service_name = data.get('service_name')
        force_reanalyze = data.get('force_reanalyze', False)
        
        # 检查视频是否存在
        video = Video.query.filter_by(bvid=bvid).first()
        if not video:
            return APIResponse.error("Video not found in database", 404, "VIDEO_NOT_FOUND")
        
        # 获取字幕
        subtitle = Subtitle.query.filter_by(
            video_id=video.id,
            language=language
        ).first()
        
        if not subtitle:
            return APIResponse.error(f"Subtitle not found for language: {language}", 404, "SUBTITLE_NOT_FOUND")
        
        # 检查是否已有分析结果
        if not force_reanalyze:
            existing_analysis = Analysis.query.filter_by(
                video_id=video.id,
                subtitle_id=subtitle.id
            ).order_by(Analysis.created_at.desc()).first()
            
            if existing_analysis:
                # 返回现有分析结果
                return APIResponse.success({
                    'analysis': existing_analysis.to_dict(),
                    'is_cached': True
                }, "Analysis result retrieved from cache")
        
        # 执行分析
        analyzer_instance = get_analyzer()
        
        # 在异步环境中运行分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            analysis_result = loop.run_until_complete(
                analyzer_instance.analyze_subtitle(
                    subtitle.content,
                    subtitle.format,
                    service_name
                )
            )
        finally:
            loop.close()
        
        # 保存分析结果
        analysis = Analysis(
            video_id=video.id,
            subtitle_id=subtitle.id,
            summary=analysis_result.summary,
            analysis_time=analysis_result.analysis_time,
            model_used=analysis_result.model_used
        )
        
        # 设置分析数据
        analysis.set_key_points(analysis_result.key_points)
        analysis.set_categories(analysis_result.categories)
        analysis.set_tags(analysis_result.tags)
        
        db.session.add(analysis)
        db.session.flush()
        
        # 创建知识条目
        knowledge_entries = []
        for entry_data in analysis_result.knowledge_entries:
            from bilibili_analyzer.models import KnowledgeEntry
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title=entry_data.get('title', ''),
                content=entry_data.get('content', ''),
                knowledge_type=entry_data.get('type', 'concept'),
                importance=entry_data.get('importance', 1)
            )
            
            # 添加标签
            tags = entry_data.get('tags', [])
            for tag_name in tags:
                from bilibili_analyzer.models import get_or_create_tag
                tag = get_or_create_tag(tag_name)
                if tag not in knowledge_entry.tags:
                    knowledge_entry.tags.append(tag)
            
            db.session.add(knowledge_entry)
            knowledge_entries.append(knowledge_entry)
        
        db.session.commit()
        
        # 格式化响应
        response_data = {
            'analysis': analysis.to_dict(),
            'knowledge_entries': [
                {
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content,
                    'knowledge_type': entry.knowledge_type,
                    'importance': entry.importance,
                    'tags': [tag.name for tag in entry.tags]
                }
                for entry in knowledge_entries
            ],
            'analysis_stats': {
                'total_tokens': analysis_result.total_tokens,
                'total_cost': analysis_result.total_cost,
                'chunk_count': analysis_result.chunk_count,
                'analysis_time': analysis_result.analysis_time
            },
            'is_cached': False
        }
        
        return APIResponse.success(response_data, "Content analyzed successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error analyzing content: {e}")
        return APIResponse.error(f"Failed to analyze content: {str(e)}", 500)

@bp.route('/v1/analysis/<int:analysis_id>', methods=['GET'])
@require_rate_limit
def get_analysis_result(analysis_id):
    """获取分析结果"""
    try:
        # 获取分析结果
        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            return APIResponse.error("Analysis not found", 404, "ANALYSIS_NOT_FOUND")
        
        # 获取知识条目
        knowledge_entries = analysis.knowledge_entries.all()
        
        # 格式化响应
        response_data = {
            'analysis': analysis.to_dict(),
            'knowledge_entries': [
                {
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content,
                    'knowledge_type': entry.knowledge_type,
                    'importance': entry.importance,
                    'source_timestamp': entry.source_timestamp,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None,
                    'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                    'tags': [tag.name for tag in entry.tags]
                }
                for entry in knowledge_entries
            ]
        }
        
        return APIResponse.success(response_data, "Analysis result retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting analysis result: {e}")
        return APIResponse.error(f"Failed to get analysis result: {str(e)}", 500)

@bp.route('/v1/analysis/batch', methods=['POST'])
@require_rate_limit
def batch_analyze():
    """批量分析"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json(['bvids'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        bvids = data['bvids']
        language = data.get('language', 'zh-CN')
        service_name = data.get('service_name')
        force_reanalyze = data.get('force_reanalyze', False)
        
        if not isinstance(bvids, list) or len(bvids) == 0:
            return APIResponse.error("bvids must be a non-empty list", 400)
        
        # 限制批量分析数量
        if len(bvids) > 10:
            return APIResponse.error("Maximum 10 videos per batch analysis", 400)
        
        results = []
        errors = []
        
        for bvid in bvids:
            try:
                # 检查视频是否存在
                video = Video.query.filter_by(bvid=bvid).first()
                if not video:
                    errors.append({
                        'bvid': bvid,
                        'error': 'Video not found',
                        'code': 'VIDEO_NOT_FOUND'
                    })
                    continue
                
                # 获取字幕
                subtitle = Subtitle.query.filter_by(
                    video_id=video.id,
                    language=language
                ).first()
                
                if not subtitle:
                    errors.append({
                        'bvid': bvid,
                        'error': f'Subtitle not found for language: {language}',
                        'code': 'SUBTITLE_NOT_FOUND'
                    })
                    continue
                
                # 检查是否已有分析结果
                if not force_reanalyze:
                    existing_analysis = Analysis.query.filter_by(
                        video_id=video.id,
                        subtitle_id=subtitle.id
                    ).order_by(Analysis.created_at.desc()).first()
                    
                    if existing_analysis:
                        results.append({
                            'bvid': bvid,
                            'analysis_id': existing_analysis.id,
                            'status': 'cached',
                            'message': 'Analysis result retrieved from cache'
                        })
                        continue
                
                # 执行分析
                analyzer_instance = get_analyzer()
                
                # 在异步环境中运行分析
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    analysis_result = loop.run_until_complete(
                        analyzer_instance.analyze_subtitle(
                            subtitle.content,
                            subtitle.format,
                            service_name
                        )
                    )
                finally:
                    loop.close()
                
                # 保存分析结果
                analysis = Analysis(
                    video_id=video.id,
                    subtitle_id=subtitle.id,
                    summary=analysis_result.summary,
                    analysis_time=analysis_result.analysis_time,
                    model_used=analysis_result.model_used
                )
                
                analysis.set_key_points(analysis_result.key_points)
                analysis.set_categories(analysis_result.categories)
                analysis.set_tags(analysis_result.tags)
                
                db.session.add(analysis)
                db.session.flush()
                
                # 创建知识条目
                for entry_data in analysis_result.knowledge_entries:
                    from bilibili_analyzer.models import KnowledgeEntry
                    knowledge_entry = KnowledgeEntry(
                        analysis_id=analysis.id,
                        title=entry_data.get('title', ''),
                        content=entry_data.get('content', ''),
                        knowledge_type=entry_data.get('type', 'concept'),
                        importance=entry_data.get('importance', 1)
                    )
                    
                    # 添加标签
                    tags = entry_data.get('tags', [])
                    for tag_name in tags:
                        from bilibili_analyzer.models import get_or_create_tag
                        tag = get_or_create_tag(tag_name)
                        if tag not in knowledge_entry.tags:
                            knowledge_entry.tags.append(tag)
                    
                    db.session.add(knowledge_entry)
                
                db.session.commit()
                
                results.append({
                    'bvid': bvid,
                    'analysis_id': analysis.id,
                    'status': 'completed',
                    'message': 'Analysis completed successfully'
                })
                
            except Exception as e:
                current_app.logger.error(f"Error analyzing video {bvid}: {e}")
                errors.append({
                    'bvid': bvid,
                    'error': str(e),
                    'code': 'ANALYSIS_ERROR'
                })
        
        # 格式化响应
        response_data = {
            'results': results,
            'errors': errors,
            'summary': {
                'total': len(bvids),
                'successful': len(results),
                'failed': len(errors)
            }
        }
        
        return APIResponse.success(response_data, "Batch analysis completed")
        
    except Exception as e:
        current_app.logger.error(f"Error in batch analysis: {e}")
        return APIResponse.error(f"Failed to perform batch analysis: {str(e)}", 500)

@bp.route('/v1/analyses', methods=['GET'])
@require_rate_limit
def list_analyses():
    """获取分析结果列表"""
    try:
        # 获取分页参数
        page, per_page = APIValidator.validate_pagination_params()
        
        # 获取查询参数
        video_id = request.args.get('video_id', type=int)
        model_used = request.args.get('model_used')
        min_analysis_time = request.args.get('min_analysis_time', type=float)
        
        # 构建查询
        query = Analysis.query
        
        # 视频过滤
        if video_id:
            query = query.filter(Analysis.video_id == video_id)
        
        # 模型过滤
        if model_used:
            query = query.filter(Analysis.model_used == model_used)
        
        # 分析时间过滤
        if min_analysis_time:
            query = query.filter(Analysis.analysis_time >= min_analysis_time)
        
        # 分页查询
        pagination = query.order_by(Analysis.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 格式化响应
        analyses_data = []
        for analysis in pagination.items:
            analysis_data = analysis.to_dict()
            
            # 添加视频信息
            if analysis.video:
                analysis_data['video'] = {
                    'id': analysis.video.id,
                    'bvid': analysis.video.bvid,
                    'title': analysis.video.title,
                    'author': analysis.video.author
                }
            
            # 添加字幕信息
            if analysis.subtitle:
                analysis_data['subtitle'] = {
                    'id': analysis.subtitle.id,
                    'language': analysis.subtitle.language,
                    'format': analysis.subtitle.format
                }
            
            # 添加知识条目统计
            analysis_data['knowledge_entries_count'] = analysis.knowledge_entries.count()
            
            analyses_data.append(analysis_data)
        
        return APIResponse.paginated(
            analyses_data,
            pagination.total,
            page,
            per_page,
            "Analyses retrieved successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Error listing analyses: {e}")
        return APIResponse.error(f"Failed to list analyses: {str(e)}", 500)

@bp.route('/v1/analysis/<int:analysis_id>/knowledge', methods=['GET'])
@require_rate_limit
def get_analysis_knowledge(analysis_id):
    """获取分析结果的知识条目"""
    try:
        # 获取分析结果
        analysis = Analysis.query.get(analysis_id)
        if not analysis:
            return APIResponse.error("Analysis not found", 404, "ANALYSIS_NOT_FOUND")
        
        # 获取知识条目
        knowledge_entries = analysis.knowledge_entries.all()
        
        # 格式化响应
        knowledge_data = []
        for entry in knowledge_entries:
            knowledge_data.append({
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'knowledge_type': entry.knowledge_type,
                'importance': entry.importance,
                'source_timestamp': entry.source_timestamp,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                'tags': [tag.name for tag in entry.tags]
            })
        
        return APIResponse.success(knowledge_data, "Knowledge entries retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting analysis knowledge: {e}")
        return APIResponse.error(f"Failed to get analysis knowledge: {str(e)}", 500)