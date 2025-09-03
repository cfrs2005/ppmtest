"""
JSON导出器
"""

import json
from typing import List, Dict, Any

from .base_exporter import BaseExporter
from ..models import KnowledgeEntry


class JsonExporter(BaseExporter):
    """JSON导出器"""
    
    def export(self, entries: List[KnowledgeEntry], metadata: Dict[str, Any] = None) -> str:
        """
        导出为JSON格式
        
        Args:
            entries: 知识条目列表
            metadata: 元数据
            
        Returns:
            str: JSON格式的导出内容
        """
        # 构建导出数据
        export_data = self._build_metadata(entries, metadata)
        export_data['entries'] = [self._format_entry(entry) for entry in entries]
        
        # 添加统计信息
        export_data['statistics'] = self._generate_statistics(entries)
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.json'
    
    def get_content_type(self) -> str:
        """获取内容类型"""
        return 'application/json'
    
    def _generate_statistics(self, entries: List[KnowledgeEntry]) -> Dict[str, Any]:
        """
        生成统计信息
        
        Args:
            entries: 知识条目列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        from collections import defaultdict
        
        # 按类型统计
        type_counts = defaultdict(int)
        importance_counts = defaultdict(int)
        tag_counts = defaultdict(int)
        
        for entry in entries:
            type_counts[entry.knowledge_type] += 1
            importance_counts[entry.importance] += 1
            for tag in entry.tags:
                tag_counts[tag.name] += 1
        
        return {
            'by_type': dict(type_counts),
            'by_importance': dict(importance_counts),
            'popular_tags': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20])
        }