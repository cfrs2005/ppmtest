"""
知识库管理API路由
"""

import json
from datetime import datetime
from flask import request, current_app, send_file
from . import bp
from .utils import APIResponse, APIValidator, require_rate_limit
from bilibili_analyzer.models import db, KnowledgeEntry, Analysis, Tag
from bilibili_analyzer.managers.knowledge_manager import KnowledgeManager
from bilibili_analyzer.services.search import SearchService
import tempfile
import os

# 初始化知识库管理器
knowledge_manager = KnowledgeManager(SearchService())

@bp.route('/v1/knowledge/search', methods=['GET'])
@require_rate_limit
def search_knowledge():
    """搜索知识库"""
    try:
        # 验证查询参数
        is_valid, error_msg, params = APIValidator.validate_query_params(['q'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        query = params['q']
        limit = params.get('limit', 50, type=int)
        offset = params.get('offset', 0, type=int)
        
        # 限制搜索结果数量
        limit = min(limit, 100)
        
        # 执行搜索
        results = knowledge_manager.search_knowledge(query, limit, offset)
        
        return APIResponse.success({
            'query': query,
            'results': results,
            'total': len(results),
            'limit': limit,
            'offset': offset
        }, "Knowledge search completed")
        
    except Exception as e:
        current_app.logger.error(f"Error searching knowledge: {e}")
        return APIResponse.error(f"Failed to search knowledge: {str(e)}", 500)

@bp.route('/v1/knowledge', methods=['POST'])
@require_rate_limit
def create_knowledge_entry():
    """创建知识条目"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json(['title', 'content'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        title = data['title']
        content = data['content']
        knowledge_type = data.get('knowledge_type', 'concept')
        importance = data.get('importance', 1)
        analysis_id = data.get('analysis_id')
        source_timestamp = data.get('source_timestamp')
        tags = data.get('tags', [])
        
        # 验证重要性等级
        if not 1 <= importance <= 5:
            return APIResponse.error("Importance must be between 1 and 5", 400)
        
        # 如果指定了分析ID，验证分析是否存在
        if analysis_id:
            analysis = Analysis.query.get(analysis_id)
            if not analysis:
                return APIResponse.error("Analysis not found", 404, "ANALYSIS_NOT_FOUND")
        
        # 创建知识条目
        knowledge_entry = KnowledgeEntry(
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            importance=importance,
            analysis_id=analysis_id,
            source_timestamp=source_timestamp
        )
        
        db.session.add(knowledge_entry)
        db.session.flush()
        
        # 添加标签
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            if tag not in knowledge_entry.tags:
                knowledge_entry.tags.append(tag)
        
        db.session.commit()
        
        # 更新搜索索引
        knowledge_manager.search_service.index_knowledge_entry(knowledge_entry)
        
        # 格式化响应
        response_data = {
            'id': knowledge_entry.id,
            'title': knowledge_entry.title,
            'content': knowledge_entry.content,
            'knowledge_type': knowledge_entry.knowledge_type,
            'importance': knowledge_entry.importance,
            'source_timestamp': knowledge_entry.source_timestamp,
            'created_at': knowledge_entry.created_at.isoformat() if knowledge_entry.created_at else None,
            'updated_at': knowledge_entry.updated_at.isoformat() if knowledge_entry.updated_at else None,
            'tags': [tag.name for tag in knowledge_entry.tags],
            'analysis_id': knowledge_entry.analysis_id
        }
        
        return APIResponse.success(response_data, "Knowledge entry created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating knowledge entry: {e}")
        return APIResponse.error(f"Failed to create knowledge entry: {str(e)}", 500)

@bp.route('/v1/knowledge/<int:entry_id>', methods=['GET'])
@require_rate_limit
def get_knowledge_entry(entry_id):
    """获取知识条目"""
    try:
        # 获取知识条目
        knowledge_entry = KnowledgeEntry.query.get(entry_id)
        if not knowledge_entry:
            return APIResponse.error("Knowledge entry not found", 404, "KNOWLEDGE_NOT_FOUND")
        
        # 格式化响应
        response_data = {
            'id': knowledge_entry.id,
            'title': knowledge_entry.title,
            'content': knowledge_entry.content,
            'knowledge_type': knowledge_entry.knowledge_type,
            'importance': knowledge_entry.importance,
            'source_timestamp': knowledge_entry.source_timestamp,
            'created_at': knowledge_entry.created_at.isoformat() if knowledge_entry.created_at else None,
            'updated_at': knowledge_entry.updated_at.isoformat() if knowledge_entry.updated_at else None,
            'tags': [tag.name for tag in knowledge_entry.tags],
            'analysis_id': knowledge_entry.analysis_id,
            'analysis': None,
            'related_entries': []
        }
        
        # 添加分析信息
        if knowledge_entry.analysis:
            response_data['analysis'] = {
                'id': knowledge_entry.analysis.id,
                'summary': knowledge_entry.analysis.summary,
                'model_used': knowledge_entry.analysis.model_used,
                'created_at': knowledge_entry.analysis.created_at.isoformat() if knowledge_entry.analysis.created_at else None,
                'video': {
                    'id': knowledge_entry.analysis.video.id,
                    'bvid': knowledge_entry.analysis.video.bvid,
                    'title': knowledge_entry.analysis.video.title,
                    'author': knowledge_entry.analysis.video.author
                } if knowledge_entry.analysis.video else None
            }
        
        # 获取相关条目
        related_entries = knowledge_manager.get_related_entries(entry_id, limit=5)
        response_data['related_entries'] = related_entries
        
        return APIResponse.success(response_data, "Knowledge entry retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting knowledge entry: {e}")
        return APIResponse.error(f"Failed to get knowledge entry: {str(e)}", 500)

@bp.route('/v1/knowledge/<int:entry_id>', methods=['PUT'])
@require_rate_limit
def update_knowledge_entry(entry_id):
    """更新知识条目"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json()
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        # 获取知识条目
        knowledge_entry = KnowledgeEntry.query.get(entry_id)
        if not knowledge_entry:
            return APIResponse.error("Knowledge entry not found", 404, "KNOWLEDGE_NOT_FOUND")
        
        # 更新字段
        updates = {}
        if 'title' in data:
            updates['title'] = data['title']
        if 'content' in data:
            updates['content'] = data['content']
        if 'knowledge_type' in data:
            updates['knowledge_type'] = data['knowledge_type']
        if 'importance' in data:
            importance = data['importance']
            if not 1 <= importance <= 5:
                return APIResponse.error("Importance must be between 1 and 5", 400)
            updates['importance'] = importance
        if 'source_timestamp' in data:
            updates['source_timestamp'] = data['source_timestamp']
        if 'tags' in data:
            updates['tags'] = data['tags']
        
        # 执行更新
        updated_entry = knowledge_manager.update_knowledge_entry(entry_id, updates)
        
        return APIResponse.success(updated_entry, "Knowledge entry updated successfully")
        
    except ValueError as e:
        return APIResponse.error(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Error updating knowledge entry: {e}")
        return APIResponse.error(f"Failed to update knowledge entry: {str(e)}", 500)

@bp.route('/v1/knowledge/<int:entry_id>', methods=['DELETE'])
@require_rate_limit
def delete_knowledge_entry(entry_id):
    """删除知识条目"""
    try:
        # 获取知识条目
        knowledge_entry = KnowledgeEntry.query.get(entry_id)
        if not knowledge_entry:
            return APIResponse.error("Knowledge entry not found", 404, "KNOWLEDGE_NOT_FOUND")
        
        # 删除知识条目
        success = knowledge_manager.delete_knowledge_entry(entry_id)
        
        if success:
            return APIResponse.success(None, "Knowledge entry deleted successfully")
        else:
            return APIResponse.error("Failed to delete knowledge entry", 500)
        
    except ValueError as e:
        return APIResponse.error(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Error deleting knowledge entry: {e}")
        return APIResponse.error(f"Failed to delete knowledge entry: {str(e)}", 500)

@bp.route('/v1/knowledge/export', methods=['GET'])
@require_rate_limit
def export_knowledge():
    """导出知识库"""
    try:
        # 验证查询参数
        is_valid, error_msg, params = APIValidator.validate_query_params()
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        format_type = params.get('format', 'json').lower()
        knowledge_type = params.get('knowledge_type')
        importance_min = params.get('importance_min', type=int)
        importance_max = params.get('importance_max', type=int)
        tags = params.get('tags', '').split(',') if params.get('tags') else None
        
        # 构建过滤条件
        filters = {}
        if knowledge_type:
            filters['knowledge_type'] = knowledge_type
        if importance_min is not None:
            filters['importance_min'] = importance_min
        if importance_max is not None:
            filters['importance_max'] = importance_max
        if tags:
            filters['tags'] = [tag.strip() for tag in tags if tag.strip()]
        
        # 导出数据
        exported_data = knowledge_manager.export_knowledge(format_type, filters)
        
        # 根据格式返回响应
        if format_type == 'json':
            return current_app.response_class(
                exported_data,
                mimetype='application/json',
                headers={
                    'Content-Disposition': 'attachment; filename=knowledge_base.json'
                }
            )
        elif format_type == 'markdown':
            return current_app.response_class(
                exported_data,
                mimetype='text/markdown',
                headers={
                    'Content-Disposition': 'attachment; filename=knowledge_base.md'
                }
            )
        elif format_type == 'csv':
            return current_app.response_class(
                exported_data,
                mimetype='text/csv',
                headers={
                    'Content-Disposition': 'attachment; filename=knowledge_base.csv'
                }
            )
        else:
            return APIResponse.error(f"Unsupported export format: {format_type}", 400)
        
    except Exception as e:
        current_app.logger.error(f"Error exporting knowledge: {e}")
        return APIResponse.error(f"Failed to export knowledge: {str(e)}", 500)

@bp.route('/v1/knowledge', methods=['GET'])
@require_rate_limit
def list_knowledge_entries():
    """获取知识条目列表"""
    try:
        # 获取分页参数
        page, per_page = APIValidator.validate_pagination_params()
        
        # 获取查询参数
        knowledge_type = request.args.get('knowledge_type')
        importance_min = request.args.get('importance_min', type=int)
        importance_max = request.args.get('importance_max', type=int)
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else None
        search = request.args.get('search')
        
        # 构建查询
        query = KnowledgeEntry.query
        
        # 类型过滤
        if knowledge_type:
            query = query.filter(KnowledgeEntry.knowledge_type == knowledge_type)
        
        # 重要性过滤
        if importance_min is not None:
            query = query.filter(KnowledgeEntry.importance >= importance_min)
        if importance_max is not None:
            query = query.filter(KnowledgeEntry.importance <= importance_max)
        
        # 标签过滤
        if tags:
            query = query.join(KnowledgeEntry.tags).filter(Tag.name.in_([tag.strip() for tag in tags if tag.strip()]))
        
        # 搜索过滤
        if search:
            query = query.filter(
                db.or_(
                    KnowledgeEntry.title.contains(search),
                    KnowledgeEntry.content.contains(search)
                )
            )
        
        # 分页查询
        pagination = query.order_by(KnowledgeEntry.importance.desc(), KnowledgeEntry.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # 格式化响应
        entries_data = []
        for entry in pagination.items:
            entry_data = {
                'id': entry.id,
                'title': entry.title,
                'content': entry.content[:200] + '...' if len(entry.content) > 200 else entry.content,
                'knowledge_type': entry.knowledge_type,
                'importance': entry.importance,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                'tags': [tag.name for tag in entry.tags],
                'analysis_id': entry.analysis_id
            }
            
            # 添加分析信息
            if entry.analysis:
                entry_data['analysis'] = {
                    'id': entry.analysis.id,
                    'summary': entry.analysis.summary[:100] + '...' if len(entry.analysis.summary) > 100 else entry.analysis.summary,
                    'video': {
                        'id': entry.analysis.video.id,
                        'bvid': entry.analysis.video.bvid,
                        'title': entry.analysis.video.title
                    } if entry.analysis.video else None
                }
            
            entries_data.append(entry_data)
        
        return APIResponse.paginated(
            entries_data,
            pagination.total,
            page,
            per_page,
            "Knowledge entries retrieved successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Error listing knowledge entries: {e}")
        return APIResponse.error(f"Failed to list knowledge entries: {str(e)}", 500)

@bp.route('/v1/knowledge/stats', methods=['GET'])
@require_rate_limit
def get_knowledge_stats():
    """获取知识库统计信息"""
    try:
        stats = knowledge_manager.get_knowledge_stats()
        
        return APIResponse.success(stats, "Knowledge base statistics retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting knowledge stats: {e}")
        return APIResponse.error(f"Failed to get knowledge stats: {str(e)}", 500)

@bp.route('/v1/knowledge/<int:entry_id>/related', methods=['GET'])
@require_rate_limit
def get_related_knowledge_entries(entry_id):
    """获取相关知识条目"""
    try:
        limit = request.args.get('limit', 5, type=int)
        limit = min(limit, 20)  # 限制最大数量
        
        related_entries = knowledge_manager.get_related_entries(entry_id, limit)
        
        return APIResponse.success(related_entries, "Related knowledge entries retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting related knowledge entries: {e}")
        return APIResponse.error(f"Failed to get related knowledge entries: {str(e)}", 500)