"""
基础导出器抽象类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import KnowledgeEntry


class BaseExporter(ABC):
    """基础导出器抽象类"""
    
    def __init__(self):
        """初始化导出器"""
        self.export_time = datetime.utcnow()
    
    @abstractmethod
    def export(self, entries: List[KnowledgeEntry], metadata: Dict[str, Any] = None) -> str:
        """
        导出知识条目
        
        Args:
            entries: 知识条目列表
            metadata: 元数据
            
        Returns:
            str: 导出的内容
        """
        pass
    
    def get_file_extension(self) -> str:
        """
        获取文件扩展名
        
        Returns:
            str: 文件扩展名
        """
        return '.txt'
    
    def get_content_type(self) -> str:
        """
        获取内容类型
        
        Returns:
            str: 内容类型
        """
        return 'text/plain'
    
    def _build_metadata(self, entries: List[KnowledgeEntry], additional_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        构建元数据
        
        Args:
            entries: 知识条目列表
            additional_metadata: 额外的元数据
            
        Returns:
            Dict[str, Any]: 完整的元数据
        """
        metadata = {
            'export_time': self.export_time.isoformat(),
            'total_entries': len(entries),
            'exporter': self.__class__.__name__
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata
    
    def _format_entry(self, entry: KnowledgeEntry) -> Dict[str, Any]:
        """
        格式化单个知识条目
        
        Args:
            entry: 知识条目
            
        Returns:
            Dict[str, Any]: 格式化的条目数据
        """
        return {
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