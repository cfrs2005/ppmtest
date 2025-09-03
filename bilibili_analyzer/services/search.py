"""
搜索服务 - 全文搜索和标签搜索功能
"""

import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func, or_, and_
from sqlalchemy.dialects.sqlite import json as sqlite_json

from ..models import db, KnowledgeEntry, Analysis, Tag, knowledge_tags

logger = logging.getLogger(__name__)


class SearchService:
    """搜索服务"""
    
    def __init__(self):
        """初始化搜索服务"""
        self._init_fts_tables()
    
    def _init_fts_tables(self):
        """初始化FTS5虚拟表"""
        try:
            # 检查FTS表是否存在
            result = db.session.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_entries_fts'"
            )).fetchone()
            
            if not result:
                # 创建FTS5虚拟表
                db.session.execute(text("""
                    CREATE VIRTUAL TABLE knowledge_entries_fts 
                    USING fts5(
                        title,
                        content,
                        knowledge_type,
                        tags,
                        content='knowledge_entries',
                        content_rowid='id'
                    )
                """))
                
                # 创建触发器保持同步
                db.session.execute(text("""
                    CREATE TRIGGER knowledge_entries_fts_insert 
                    AFTER INSERT ON knowledge_entries
                    BEGIN
                        INSERT INTO knowledge_entries_fts(id, title, content, knowledge_type, tags)
                        VALUES (
                            new.id,
                            new.title,
                            new.content,
                            new.knowledge_type,
                            (SELECT GROUP_CONCAT(tags.name, ' ') 
                             FROM tags 
                             JOIN knowledge_tags ON tags.id = knowledge_tags.tag_id 
                             WHERE knowledge_tags.knowledge_entry_id = new.id)
                        );
                    END;
                """))
                
                db.session.execute(text("""
                    CREATE TRIGGER knowledge_entries_fts_delete 
                    AFTER DELETE ON knowledge_entries
                    BEGIN
                        DELETE FROM knowledge_entries_fts WHERE id = old.id;
                    END;
                """))
                
                db.session.execute(text("""
                    CREATE TRIGGER knowledge_entries_fts_update 
                    AFTER UPDATE ON knowledge_entries
                    BEGIN
                        DELETE FROM knowledge_entries_fts WHERE id = old.id;
                        INSERT INTO knowledge_entries_fts(id, title, content, knowledge_type, tags)
                        VALUES (
                            new.id,
                            new.title,
                            new.content,
                            new.knowledge_type,
                            (SELECT GROUP_CONCAT(tags.name, ' ') 
                             FROM tags 
                             JOIN knowledge_tags ON tags.id = knowledge_tags.tag_id 
                             WHERE knowledge_tags.knowledge_entry_id = new.id)
                        );
                    END;
                """))
                
                db.session.commit()
                logger.info("FTS5虚拟表创建成功")
            else:
                logger.info("FTS5虚拟表已存在")
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"初始化FTS5表失败: {e}")
            raise
    
    def search(self, query: str, limit: int = 50, offset: int = 0, 
               search_type: str = 'fulltext', filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 搜索查询字符串
            limit: 结果限制数量
            offset: 偏移量
            search_type: 搜索类型 (fulltext, tags, combined)
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            if search_type == 'fulltext':
                return self._fulltext_search(query, limit, offset, filters)
            elif search_type == 'tags':
                return self._tag_search(query, limit, offset, filters)
            elif search_type == 'combined':
                return self._combined_search(query, limit, offset, filters)
            else:
                raise ValueError(f"不支持的搜索类型: {search_type}")
                
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def _fulltext_search(self, query: str, limit: int = 50, offset: int = 0, 
                        filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """全文搜索"""
        try:
            # 构建FTS5查询
            fts_query = text("""
                SELECT ke.*, kefts.rank as relevance_score
                FROM knowledge_entries ke
                JOIN knowledge_entries_fts kefts ON ke.id = kefts.id
                WHERE knowledge_entries_fts MATCH :query
                ORDER BY kefts.rank
                LIMIT :limit OFFSET :offset
            """)
            
            result = db.session.execute(fts_query, {
                'query': query,
                'limit': limit,
                'offset': offset
            }).fetchall()
            
            # 转换为字典列表
            results = []
            for row in result:
                entry = KnowledgeEntry.query.get(row.id)
                results.append({
                    'knowledge_entry': entry,
                    'relevance_score': row.relevance_score
                })
            
            return results
            
        except Exception as e:
            logger.error(f"全文搜索失败: {e}")
            return []
    
    def _tag_search(self, query: str, limit: int = 50, offset: int = 0, 
                   filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """标签搜索"""
        try:
            # 解析查询中的标签
            tags = [tag.strip() for tag in query.split() if tag.strip()]
            
            if not tags:
                return []
            
            # 构建查询
            base_query = KnowledgeEntry.query.join(KnowledgeEntry.tags).filter(
                Tag.name.in_(tags)
            )
            
            # 应用过滤条件
            if filters:
                if 'knowledge_type' in filters:
                    base_query = base_query.filter(KnowledgeEntry.knowledge_type == filters['knowledge_type'])
                if 'importance_min' in filters:
                    base_query = base_query.filter(KnowledgeEntry.importance >= filters['importance_min'])
            
            # 按匹配的标签数量排序
            query = base_query.group_by(KnowledgeEntry.id).order_by(
                func.count(Tag.id).desc(),
                KnowledgeEntry.importance.desc(),
                KnowledgeEntry.created_at.desc()
            )
            
            entries = query.offset(offset).limit(limit).all()
            
            # 计算相关性分数
            results = []
            for entry in entries:
                entry_tags = [tag.name for tag in entry.tags]
                matched_tags = len(set(tags) & set(entry_tags))
                results.append({
                    'knowledge_entry': entry,
                    'relevance_score': matched_tags / len(tags)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"标签搜索失败: {e}")
            return []
    
    def _combined_search(self, query: str, limit: int = 50, offset: int = 0, 
                        filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """组合搜索"""
        try:
            # 执行全文搜索
            fulltext_results = self._fulltext_search(query, limit * 2, 0, filters)
            
            # 执行标签搜索
            tag_results = self._tag_search(query, limit * 2, 0, filters)
            
            # 合并结果并去重
            seen_ids = set()
            combined_results = []
            
            # 添加全文搜索结果
            for result in fulltext_results:
                entry_id = result['knowledge_entry'].id
                if entry_id not in seen_ids:
                    combined_results.append(result)
                    seen_ids.add(entry_id)
            
            # 添加标签搜索结果
            for result in tag_results:
                entry_id = result['knowledge_entry'].id
                if entry_id not in seen_ids:
                    combined_results.append(result)
                    seen_ids.add(entry_id)
            
            # 按相关性分数排序
            combined_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # 应用分页
            return combined_results[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"组合搜索失败: {e}")
            return []
    
    def search_by_type(self, knowledge_type: str, query: str = None, 
                      limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        按类型搜索
        
        Args:
            knowledge_type: 知识类型
            query: 搜索查询字符串
            limit: 结果限制数量
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果
        """
        try:
            base_query = KnowledgeEntry.query.filter(
                KnowledgeEntry.knowledge_type == knowledge_type
            )
            
            if query:
                # 如果有查询字符串，使用FTS搜索
                fts_query = text("""
                    SELECT ke.*, kefts.rank as relevance_score
                    FROM knowledge_entries ke
                    JOIN knowledge_entries_fts kefts ON ke.id = kefts.id
                    WHERE ke.knowledge_type = :type AND knowledge_entries_fts MATCH :query
                    ORDER BY kefts.rank
                    LIMIT :limit OFFSET :offset
                """)
                
                result = db.session.execute(fts_query, {
                    'type': knowledge_type,
                    'query': query,
                    'limit': limit,
                    'offset': offset
                }).fetchall()
                
                results = []
                for row in result:
                    entry = KnowledgeEntry.query.get(row.id)
                    results.append({
                        'knowledge_entry': entry,
                        'relevance_score': row.relevance_score
                    })
                
                return results
            else:
                # 如果没有查询字符串，返回该类型的所有条目
                entries = base_query.order_by(
                    KnowledgeEntry.importance.desc(),
                    KnowledgeEntry.created_at.desc()
                ).offset(offset).limit(limit).all()
                
                return [{
                    'knowledge_entry': entry,
                    'relevance_score': entry.importance
                } for entry in entries]
                
        except Exception as e:
            logger.error(f"按类型搜索失败: {e}")
            return []
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取搜索建议
        
        Args:
            query: 查询字符串
            limit: 建议数量限制
            
        Returns:
            List[Dict[str, Any]]: 搜索建议
        """
        try:
            suggestions = []
            
            # 标题建议
            title_suggestions = db.session.execute(text("""
                SELECT DISTINCT title, id
                FROM knowledge_entries_fts
                WHERE title MATCH :query || '*'
                LIMIT :limit
            """), {'query': query, 'limit': limit}).fetchall()
            
            for row in title_suggestions:
                suggestions.append({
                    'type': 'title',
                    'text': row.title,
                    'entry_id': row.id
                })
            
            # 标签建议
            tag_suggestions = Tag.query.filter(
                Tag.name.ilike(f'{query}%')
            ).limit(limit).all()
            
            for tag in tag_suggestions:
                suggestions.append({
                    'type': 'tag',
                    'text': tag.name,
                    'tag_id': tag.id
                })
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}")
            return []
    
    def index_analysis_result(self, analysis_result, analysis_id: int):
        """
        索引分析结果
        
        Args:
            analysis_result: 分析结果对象
            analysis_id: 分析记录ID
        """
        try:
            # FTS5会通过触发器自动索引，这里不需要额外操作
            logger.debug(f"分析结果 {analysis_id} 已自动索引")
            
        except Exception as e:
            logger.error(f"索引分析结果失败: {e}")
    
    def update_knowledge_entry(self, entry: KnowledgeEntry):
        """
        更新知识条目索引
        
        Args:
            entry: 知识条目对象
        """
        try:
            # FTS5会通过触发器自动更新，这里不需要额外操作
            logger.debug(f"知识条目 {entry.id} 已自动更新索引")
            
        except Exception as e:
            logger.error(f"更新知识条目索引失败: {e}")
    
    def delete_knowledge_entry(self, entry_id: int):
        """
        删除知识条目索引
        
        Args:
            entry_id: 知识条目ID
        """
        try:
            # FTS5会通过触发器自动删除，这里不需要额外操作
            logger.debug(f"知识条目 {entry_id} 已自动删除索引")
            
        except Exception as e:
            logger.error(f"删除知识条目索引失败: {e}")
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        获取搜索统计信息
        
        Returns:
            Dict[str, Any]: 搜索统计信息
        """
        try:
            # 总条目数
            total_entries = KnowledgeEntry.query.count()
            
            # 总标签数
            total_tags = Tag.query.count()
            
            # 搜索日志统计（如果有的话）
            search_stats = {
                'total_entries': total_entries,
                'total_tags': total_tags,
                'fts_enabled': True
            }
            
            return search_stats
            
        except Exception as e:
            logger.error(f"获取搜索统计失败: {e}")
            return {}
    
    def rebuild_fts_index(self):
        """
        重建FTS索引
        """
        try:
            logger.info("开始重建FTS索引")
            
            # 删除现有FTS表
            db.session.execute(text("DROP TABLE IF EXISTS knowledge_entries_fts"))
            
            # 删除触发器
            db.session.execute(text("DROP TRIGGER IF EXISTS knowledge_entries_fts_insert"))
            db.session.execute(text("DROP TRIGGER IF EXISTS knowledge_entries_fts_delete"))
            db.session.execute(text("DROP TRIGGER IF EXISTS knowledge_entries_fts_update"))
            
            # 重新创建FTS表
            self._init_fts_tables()
            
            logger.info("FTS索引重建完成")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"重建FTS索引失败: {e}")
            raise