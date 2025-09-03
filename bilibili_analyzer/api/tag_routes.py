"""
标签系统API路由
"""

from flask import request, current_app
from . import bp
from .utils import APIResponse, APIValidator, require_rate_limit
from bilibili_analyzer.models import db, Tag, KnowledgeEntry, knowledge_tags

@bp.route('/v1/tags', methods=['GET'])
@require_rate_limit
def list_tags():
    """获取标签列表"""
    try:
        # 获取分页参数
        page, per_page = APIValidator.validate_pagination_params()
        
        # 获取查询参数
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'name')  # name, created_at, usage_count
        sort_order = request.args.get('sort_order', 'asc')  # asc, desc
        
        # 构建查询
        query = Tag.query
        
        # 搜索过滤
        if search:
            query = query.filter(Tag.name.contains(search))
        
        # 排序
        if sort_by == 'usage_count':
            # 按使用次数排序
            query = query.outerjoin(Tag.knowledge_entries).group_by(Tag.id)
            if sort_order == 'desc':
                query = query.order_by(db.func.count(knowledge_tags.c.knowledge_entry_id).desc())
            else:
                query = query.order_by(db.func.count(knowledge_tags.c.knowledge_entry_id).asc())
        elif sort_by == 'created_at':
            if sort_order == 'desc':
                query = query.order_by(Tag.created_at.desc())
            else:
                query = query.order_by(Tag.created_at.asc())
        else:  # name
            if sort_order == 'desc':
                query = query.order_by(Tag.name.desc())
            else:
                query = query.order_by(Tag.name.asc())
        
        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 格式化响应
        tags_data = []
        for tag in pagination.items:
            # 计算使用次数
            usage_count = tag.knowledge_entries.count()
            
            tag_data = {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'created_at': tag.created_at.isoformat() if tag.created_at else None,
                'usage_count': usage_count
            }
            tags_data.append(tag_data)
        
        return APIResponse.paginated(
            tags_data,
            pagination.total,
            page,
            per_page,
            "Tags retrieved successfully"
        )
        
    except Exception as e:
        current_app.logger.error(f"Error listing tags: {e}")
        return APIResponse.error(f"Failed to list tags: {str(e)}", 500)

@bp.route('/v1/tags', methods=['POST'])
@require_rate_limit
def create_tag():
    """创建标签"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json(['name'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        name = data['name'].strip()
        color = data.get('color', '#007bff')
        
        # 验证名称
        if not name:
            return APIResponse.error("Tag name cannot be empty", 400)
        
        # 检查是否已存在
        existing_tag = Tag.query.filter_by(name=name).first()
        if existing_tag:
            return APIResponse.error(f"Tag '{name}' already exists", 409, "TAG_ALREADY_EXISTS")
        
        # 验证颜色格式
        if color and not color.startswith('#'):
            return APIResponse.error("Color must start with '#'", 400)
        
        # 创建标签
        tag = Tag(name=name, color=color)
        db.session.add(tag)
        db.session.commit()
        
        # 格式化响应
        response_data = {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'created_at': tag.created_at.isoformat() if tag.created_at else None,
            'usage_count': 0
        }
        
        return APIResponse.success(response_data, "Tag created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating tag: {e}")
        return APIResponse.error(f"Failed to create tag: {str(e)}", 500)

@bp.route('/v1/tags/<int:tag_id>', methods=['GET'])
@require_rate_limit
def get_tag(tag_id):
    """获取标签详情"""
    try:
        # 获取标签
        tag = Tag.query.get(tag_id)
        if not tag:
            return APIResponse.error("Tag not found", 404, "TAG_NOT_FOUND")
        
        # 计算使用次数
        usage_count = tag.knowledge_entries.count()
        
        # 获取相关的知识条目
        knowledge_entries = tag.knowledge_entries.limit(10).all()
        
        # 格式化响应
        response_data = {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'created_at': tag.created_at.isoformat() if tag.created_at else None,
            'usage_count': usage_count,
            'recent_knowledge_entries': [
                {
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content[:100] + '...' if len(entry.content) > 100 else entry.content,
                    'knowledge_type': entry.knowledge_type,
                    'importance': entry.importance,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None
                }
                for entry in knowledge_entries
            ]
        }
        
        return APIResponse.success(response_data, "Tag retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting tag: {e}")
        return APIResponse.error(f"Failed to get tag: {str(e)}", 500)

@bp.route('/v1/tags/<int:tag_id>', methods=['PUT'])
@require_rate_limit
def update_tag(tag_id):
    """更新标签"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json()
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        # 获取标签
        tag = Tag.query.get(tag_id)
        if not tag:
            return APIResponse.error("Tag not found", 404, "TAG_NOT_FOUND")
        
        # 更新字段
        if 'name' in data:
            new_name = data['name'].strip()
            if not new_name:
                return APIResponse.error("Tag name cannot be empty", 400)
            
            # 检查名称冲突
            existing_tag = Tag.query.filter_by(name=new_name).first()
            if existing_tag and existing_tag.id != tag_id:
                return APIResponse.error(f"Tag '{new_name}' already exists", 409, "TAG_ALREADY_EXISTS")
            
            tag.name = new_name
        
        if 'color' in data:
            color = data['color']
            if color and not color.startswith('#'):
                return APIResponse.error("Color must start with '#'", 400)
            tag.color = color
        
        db.session.commit()
        
        # 计算使用次数
        usage_count = tag.knowledge_entries.count()
        
        # 格式化响应
        response_data = {
            'id': tag.id,
            'name': tag.name,
            'color': tag.color,
            'created_at': tag.created_at.isoformat() if tag.created_at else None,
            'usage_count': usage_count
        }
        
        return APIResponse.success(response_data, "Tag updated successfully")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating tag: {e}")
        return APIResponse.error(f"Failed to update tag: {str(e)}", 500)

@bp.route('/v1/tags/<int:tag_id>', methods=['DELETE'])
@require_rate_limit
def delete_tag(tag_id):
    """删除标签"""
    try:
        # 获取标签
        tag = Tag.query.get(tag_id)
        if not tag:
            return APIResponse.error("Tag not found", 404, "TAG_NOT_FOUND")
        
        # 检查是否有关联的知识条目
        usage_count = tag.knowledge_entries.count()
        if usage_count > 0:
            return APIResponse.error(
                f"Cannot delete tag '{tag.name}' because it is used by {usage_count} knowledge entries",
                409,
                "TAG_IN_USE"
            )
        
        # 删除标签
        db.session.delete(tag)
        db.session.commit()
        
        return APIResponse.success(None, "Tag deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting tag: {e}")
        return APIResponse.error(f"Failed to delete tag: {str(e)}", 500)

@bp.route('/v1/knowledge/<int:entry_id>/tags', methods=['GET'])
@require_rate_limit
def get_knowledge_entry_tags(entry_id):
    """获取知识条目的标签"""
    try:
        # 获取知识条目
        knowledge_entry = KnowledgeEntry.query.get(entry_id)
        if not knowledge_entry:
            return APIResponse.error("Knowledge entry not found", 404, "KNOWLEDGE_NOT_FOUND")
        
        # 获取标签
        tags = knowledge_entry.tags.all()
        
        # 格式化响应
        tags_data = []
        for tag in tags:
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'created_at': tag.created_at.isoformat() if tag.created_at else None
            })
        
        return APIResponse.success(tags_data, "Knowledge entry tags retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting knowledge entry tags: {e}")
        return APIResponse.error(f"Failed to get knowledge entry tags: {str(e)}", 500)

@bp.route('/v1/knowledge/<int:entry_id>/tags', methods=['POST'])
@require_rate_limit
def add_knowledge_entry_tags(entry_id):
    """为知识条目添加标签"""
    try:
        # 验证请求
        is_valid, error_msg, data = APIValidator.validate_json(['tags'])
        if not is_valid:
            return APIResponse.error(error_msg, 400)
        
        tags_to_add = data['tags']
        if not isinstance(tags_to_add, list):
            return APIResponse.error("Tags must be a list", 400)
        
        # 获取知识条目
        knowledge_entry = KnowledgeEntry.query.get(entry_id)
        if not knowledge_entry:
            return APIResponse.error("Knowledge entry not found", 404, "KNOWLEDGE_NOT_FOUND")
        
        # 添加标签
        added_tags = []
        for tag_name in tags_to_add:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            
            # 获取或创建标签
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            
            # 添加到知识条目
            if tag not in knowledge_entry.tags:
                knowledge_entry.tags.append(tag)
                added_tags.append(tag)
        
        db.session.commit()
        
        # 格式化响应
        tags_data = []
        for tag in added_tags:
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'created_at': tag.created_at.isoformat() if tag.created_at else None
            })
        
        return APIResponse.success(tags_data, "Tags added to knowledge entry successfully")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding knowledge entry tags: {e}")
        return APIResponse.error(f"Failed to add knowledge entry tags: {str(e)}", 500)

@bp.route('/v1/knowledge/<int:entry_id>/tags/<int:tag_id>', methods=['DELETE'])
@require_rate_limit
def remove_knowledge_entry_tag(entry_id, tag_id):
    """从知识条目移除标签"""
    try:
        # 获取知识条目
        knowledge_entry = KnowledgeEntry.query.get(entry_id)
        if not knowledge_entry:
            return APIResponse.error("Knowledge entry not found", 404, "KNOWLEDGE_NOT_FOUND")
        
        # 获取标签
        tag = Tag.query.get(tag_id)
        if not tag:
            return APIResponse.error("Tag not found", 404, "TAG_NOT_FOUND")
        
        # 检查是否有关联
        if tag not in knowledge_entry.tags:
            return APIResponse.error("Tag is not associated with this knowledge entry", 404, "TAG_NOT_ASSOCIATED")
        
        # 移除标签
        knowledge_entry.tags.remove(tag)
        db.session.commit()
        
        return APIResponse.success(None, "Tag removed from knowledge entry successfully")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing knowledge entry tag: {e}")
        return APIResponse.error(f"Failed to remove knowledge entry tag: {str(e)}", 500)

@bp.route('/v1/tags/popular', methods=['GET'])
@require_rate_limit
def get_popular_tags():
    """获取热门标签"""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # 限制最大数量
        
        # 按使用次数排序获取热门标签
        popular_tags = db.session.query(
            Tag,
            db.func.count(knowledge_tags.c.knowledge_entry_id).label('usage_count')
        ).join(knowledge_tags).group_by(Tag.id).order_by(
            db.func.count(knowledge_tags.c.knowledge_entry_id).desc()
        ).limit(limit).all()
        
        # 格式化响应
        tags_data = []
        for tag, usage_count in popular_tags:
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'created_at': tag.created_at.isoformat() if tag.created_at else None,
                'usage_count': usage_count
            })
        
        return APIResponse.success(tags_data, "Popular tags retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error getting popular tags: {e}")
        return APIResponse.error(f"Failed to get popular tags: {str(e)}", 500)

@bp.route('/v1/tags/cleanup', methods=['POST'])
@require_rate_limit
def cleanup_unused_tags():
    """清理未使用的标签"""
    try:
        from bilibili_analyzer.models import cleanup_unused_tags
        
        # 执行清理
        cleaned_count = cleanup_unused_tags()
        
        return APIResponse.success({
            'cleaned_count': cleaned_count,
            'message': f"Cleaned up {cleaned_count} unused tags"
        }, "Unused tags cleaned up successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error cleaning up unused tags: {e}")
        return APIResponse.error(f"Failed to clean up unused tags: {str(e)}", 500)