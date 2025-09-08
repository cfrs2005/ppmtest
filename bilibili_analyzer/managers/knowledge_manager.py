"""
知识库管理器 - 管理分析结果和知识条目
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy import text, func, or_, and_
from sqlalchemy.dialects.sqlite import json as sqlite_json
from sqlalchemy.orm import joinedload, contains_eager

from ..models import db, KnowledgeEntry, Analysis, Tag, knowledge_tags, get_or_create_tag
from ..analyzers.content_analyzer import AnalysisResult
from ..services.search import SearchService

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """知识库管理器"""
    
    def __init__(self, search_service: SearchService = None):
        """
        初始化知识库管理器
        
        Args:
            search_service: 搜索服务实例
        """
        self.search_service = search_service or SearchService()
    
    def save_analysis_result(self, analysis_result: AnalysisResult) -> Analysis:
        """
        保存分析结果到数据库
        
        Args:
            analysis_result: 分析结果对象
            
        Returns:
            Analysis: 保存的分析记录
        """
        try:
            # 首先创建或获取分析记录
            analysis = Analysis(
                summary=analysis_result.summary,
                key_points=json.dumps(analysis_result.key_points, ensure_ascii=False),
                categories=json.dumps(analysis_result.categories, ensure_ascii=False),
                tags=json.dumps(analysis_result.tags, ensure_ascii=False),
                analysis_time=analysis_result.analysis_time,
                model_used=analysis_result.model_used
            )
            
            db.session.add(analysis)
            db.session.flush()  # 获取ID
            
            # 创建知识条目
            knowledge_entries = []
            for entry_data in analysis_result.knowledge_entries:
                knowledge_entry = KnowledgeEntry(
                    analysis_id=analysis.id,
                    title=entry_data.get('title', ''),
                    content=entry_data.get('content', ''),
                    knowledge_type=entry_data.get('type', 'concept'),
                    source_timestamp=entry_data.get('source_timestamp'),
                    importance=entry_data.get('importance', 1)
                )
                
                db.session.add(knowledge_entry)
                db.session.flush()  # 获取ID
                
                # 添加标签
                entry_tags = entry_data.get('tags', [])
                for tag_name in entry_tags:
                    tag = get_or_create_tag(tag_name)
                    if tag not in knowledge_entry.tags:
                        knowledge_entry.tags.append(tag)
                
                knowledge_entries.append(knowledge_entry)
            
            # 提交事务
            db.session.commit()
            
            # 更新搜索索引
            self.search_service.index_analysis_result(analysis_result, analysis.id)
            
            logger.info(f"成功保存分析结果，ID: {analysis.id}, 创建了 {len(knowledge_entries)} 个知识条目")
            return analysis
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存分析结果失败: {e}")
            raise
    
    def search_knowledge(self, query: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        搜索知识条目
        
        Args:
            query: 搜索查询字符串
            limit: 结果限制数量
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 匹配的知识条目列表
        """
        try:
            # 使用搜索服务进行全文搜索
            results = self.search_service.search(query, limit=limit, offset=offset)
            
            # 格式化结果
            formatted_results = []
            for result in results:
                entry = result['knowledge_entry']
                formatted_results.append({
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content,
                    'knowledge_type': entry.knowledge_type,
                    'importance': entry.importance,
                    'source_timestamp': entry.source_timestamp,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None,
                    'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                    'tags': [tag.name for tag in entry.tags],
                    'relevance_score': result.get('relevance_score', 0),
                    'analysis': {
                        'id': entry.analysis.id,
                        'summary': entry.analysis.summary,
                        'video': {
                            'id': entry.analysis.video.id,
                            'title': entry.analysis.video.title,
                            'bvid': entry.analysis.video.bvid
                        } if entry.analysis.video else None
                    }
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索知识条目失败: {e}")
            return []
    
    def get_knowledge_by_tags(self, tags: List[str], limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        根据标签获取知识条目
        
        Args:
            tags: 标签列表
            limit: 结果限制数量
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 匹配的知识条目列表
        """
        try:
            # 构建查询 - 使用joinedload优化关联查询
            query = KnowledgeEntry.query.options(joinedload(KnowledgeEntry.tags)).join(KnowledgeEntry.tags).filter(Tag.name.in_(tags))
            
            # 如果有多个标签，使用OR关系
            if len(tags) > 1:
                query = query.filter(Tag.name.in_(tags))
            else:
                query = query.filter(Tag.name == tags[0])
            
            # 按重要性和创建时间排序
            query = query.order_by(KnowledgeEntry.importance.desc(), KnowledgeEntry.created_at.desc())
            
            # 分页
            entries = query.offset(offset).limit(limit).all()
            
            # 格式化结果
            results = []
            for entry in entries:
                results.append({
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content,
                    'knowledge_type': entry.knowledge_type,
                    'importance': entry.importance,
                    'source_timestamp': entry.source_timestamp,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None,
                    'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                    'tags': [tag.name for tag in entry.tags],
                    'analysis': {
                        'id': entry.analysis.id,
                        'summary': entry.analysis.summary,
                        'video': {
                            'id': entry.analysis.video.id,
                            'title': entry.analysis.video.title,
                            'bvid': entry.analysis.video.bvid
                        } if entry.analysis.video else None
                    }
                })
            
            return results
            
        except Exception as e:
            logger.error(f"根据标签获取知识条目失败: {e}")
            return []
    
    def update_knowledge_entry(self, entry_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新知识条目
        
        Args:
            entry_id: 知识条目ID
            updates: 更新内容字典
            
        Returns:
            Dict[str, Any]: 更新后的知识条目
        """
        try:
            # 获取知识条目
            entry = KnowledgeEntry.query.get(entry_id)
            if not entry:
                raise ValueError(f"知识条目不存在: {entry_id}")
            
            # 更新字段
            if 'title' in updates:
                entry.title = updates['title']
            if 'content' in updates:
                entry.content = updates['content']
            if 'knowledge_type' in updates:
                entry.knowledge_type = updates['knowledge_type']
            if 'importance' in updates:
                entry.importance = updates['importance']
            if 'source_timestamp' in updates:
                entry.source_timestamp = updates['source_timestamp']
            
            # 更新时间
            entry.updated_at = datetime.utcnow()
            
            # 处理标签更新
            if 'tags' in updates:
                # 清除现有标签
                entry.tags.clear()
                
                # 添加新标签
                for tag_name in updates['tags']:
                    tag = get_or_create_tag(tag_name)
                    entry.tags.append(tag)
            
            # 保存更改
            db.session.commit()
            
            # 更新搜索索引
            self.search_service.update_knowledge_entry(entry)
            
            # 返回更新后的条目
            return {
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
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新知识条目失败: {e}")
            raise
    
    def delete_knowledge_entry(self, entry_id: int) -> bool:
        """
        删除知识条目
        
        Args:
            entry_id: 知识条目ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 获取知识条目
            entry = KnowledgeEntry.query.get(entry_id)
            if not entry:
                raise ValueError(f"知识条目不存在: {entry_id}")
            
            # 删除搜索索引
            self.search_service.delete_knowledge_entry(entry_id)
            
            # 删除条目
            db.session.delete(entry)
            db.session.commit()
            
            logger.info(f"成功删除知识条目: {entry_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除知识条目失败: {e}")
            raise
    
    def export_knowledge(self, format: str = 'json', filters: Dict[str, Any] = None) -> str:
        """
        导出知识库数据
        
        Args:
            format: 导出格式 (json, markdown, csv)
            filters: 过滤条件
            
        Returns:
            str: 导出的数据字符串
        """
        try:
            # 构建查询
            query = KnowledgeEntry.query
            
            # 应用过滤条件
            if filters:
                if 'knowledge_type' in filters:
                    query = query.filter(KnowledgeEntry.knowledge_type == filters['knowledge_type'])
                if 'importance_min' in filters:
                    query = query.filter(KnowledgeEntry.importance >= filters['importance_min'])
                if 'importance_max' in filters:
                    query = query.filter(KnowledgeEntry.importance <= filters['importance_max'])
                if 'tags' in filters:
                    query = query.join(KnowledgeEntry.tags).filter(Tag.name.in_(filters['tags']))
            
            # 获取数据
            entries = query.all()
            
            # 根据格式导出
            if format.lower() == 'json':
                return self._export_json(entries)
            elif format.lower() == 'markdown':
                return self._export_markdown(entries)
            elif format.lower() == 'csv':
                return self._export_csv(entries)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
                
        except Exception as e:
            logger.error(f"导出知识库失败: {e}")
            raise
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """
        获取知识库统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 基本统计
            total_entries = KnowledgeEntry.query.count()
            total_tags = Tag.query.count()
            total_analyses = Analysis.query.count()
            
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
            
            # 热门标签统计
            popular_tags = db.session.query(
                Tag.name,
                func.count(knowledge_tags.c.knowledge_entry_id).label('count')
            ).join(knowledge_tags).group_by(Tag.id).order_by(
                func.count(knowledge_tags.c.knowledge_entry_id).desc()
            ).limit(20).all()
            
            # 最近活动统计
            recent_entries = KnowledgeEntry.query.order_by(
                KnowledgeEntry.created_at.desc()
            ).limit(10).all()
            
            return {
                'total_entries': total_entries,
                'total_tags': total_tags,
                'total_analyses': total_analyses,
                'type_distribution': {t.knowledge_type: t.count for t in type_stats},
                'importance_distribution': {i.importance: i.count for i in importance_stats},
                'popular_tags': [{'name': t.name, 'count': t.count} for t in popular_tags],
                'recent_entries': [
                    {
                        'id': entry.id,
                        'title': entry.title,
                        'created_at': entry.created_at.isoformat() if entry.created_at else None,
                        'importance': entry.importance
                    }
                    for entry in recent_entries
                ]
            }
            
        except Exception as e:
            logger.error(f"获取知识库统计失败: {e}")
            return {}
    
    def _export_json(self, entries: List[KnowledgeEntry]) -> str:
        """导出为JSON格式"""
        data = {
            'export_time': datetime.utcnow().isoformat(),
            'total_entries': len(entries),
            'entries': []
        }
        
        for entry in entries:
            entry_data = {
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'knowledge_type': entry.knowledge_type,
                'importance': entry.importance,
                'source_timestamp': entry.source_timestamp,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                'tags': [tag.name for tag in entry.tags],
                'analysis': {
                    'id': entry.analysis.id,
                    'summary': entry.analysis.summary,
                    'video': {
                        'id': entry.analysis.video.id,
                        'title': entry.analysis.video.title,
                        'bvid': entry.analysis.video.bvid
                    } if entry.analysis.video else None
                }
            }
            data['entries'].append(entry_data)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _export_markdown(self, entries: List[KnowledgeEntry]) -> str:
        """导出为Markdown格式"""
        md_content = f"# 知识库导出\n\n"
        md_content += f"**导出时间**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md_content += f"**总条目数**: {len(entries)}\n\n"
        
        for entry in entries:
            md_content += f"## {entry.title}\n\n"
            md_content += f"**类型**: {entry.knowledge_type}\n"
            md_content += f"**重要性**: {'⭐' * entry.importance}\n"
            md_content += f"**创建时间**: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else 'N/A'}\n"
            md_content += f"**标签**: {', '.join([tag.name for tag in entry.tags])}\n\n"
            md_content += f"### 内容\n\n{entry.content}\n\n"
            
            if entry.analysis and entry.analysis.video:
                md_content += f"### 来源\n\n"
                md_content += f"- **视频**: {entry.analysis.video.title}\n"
                md_content += f"- **BV号**: {entry.analysis.video.bvid}\n"
                md_content += f"- **分析ID**: {entry.analysis.id}\n\n"
            
            md_content += "---\n\n"
        
        return md_content
    
    def _export_csv(self, entries: List[KnowledgeEntry]) -> str:
        """导出为CSV格式"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            'ID', '标题', '内容', '类型', '重要性', '创建时间', '更新时间', 
            '标签', '视频标题', 'BV号', '分析总结'
        ])
        
        # 写入数据
        for entry in entries:
            writer.writerow([
                entry.id,
                entry.title,
                entry.content.replace('\n', ' '),
                entry.knowledge_type,
                entry.importance,
                entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else '',
                entry.updated_at.strftime('%Y-%m-%d %H:%M:%S') if entry.updated_at else '',
                ', '.join([tag.name for tag in entry.tags]),
                entry.analysis.video.title if entry.analysis and entry.analysis.video else '',
                entry.analysis.video.bvid if entry.analysis and entry.analysis.video else '',
                entry.analysis.summary if entry.analysis else ''
            ])
        
        return output.getvalue()
    
    def get_related_entries(self, entry_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取相关知识条目
        
        Args:
            entry_id: 参考条目ID
            limit: 结果限制数量
            
        Returns:
            List[Dict[str, Any]]: 相关条目列表
        """
        try:
            # 获取参考条目
            reference_entry = KnowledgeEntry.query.get(entry_id)
            if not reference_entry:
                return []
            
            # 获取参考条目的标签
            reference_tags = [tag.name for tag in reference_entry.tags]
            
            # 查找共享标签的条目
            related_entries = KnowledgeEntry.query.join(KnowledgeEntry.tags).filter(
                and_(
                    Tag.name.in_(reference_tags),
                    KnowledgeEntry.id != entry_id
                )
            ).group_by(KnowledgeEntry.id).order_by(
                func.count(Tag.id).desc()
            ).limit(limit).all()
            
            # 格式化结果
            results = []
            for entry in related_entries:
                results.append({
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content[:200] + '...' if len(entry.content) > 200 else entry.content,
                    'knowledge_type': entry.knowledge_type,
                    'importance': entry.importance,
                    'created_at': entry.created_at.isoformat() if entry.created_at else None,
                    'tags': [tag.name for tag in entry.tags],
                    'relevance_score': len(set(reference_tags) & set([tag.name for tag in entry.tags]))
                })
            
            return results
            
        except Exception as e:
            logger.error(f"获取相关条目失败: {e}")
            return []
    
    def cleanup_unused_tags(self) -> int:
        """
        清理未使用的标签
        
        Returns:
            int: 清理的标签数量
        """
        try:
            # 查找未使用的标签
            unused_tags = Tag.query.outerjoin(knowledge_tags).filter(
                knowledge_tags.c.tag_id.is_(None)
            ).all()
            
            count = len(unused_tags)
            
            # 删除未使用的标签
            for tag in unused_tags:
                db.session.delete(tag)
            
            db.session.commit()
            
            logger.info(f"清理了 {count} 个未使用的标签")
            return count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"清理未使用标签失败: {e}")
            raise