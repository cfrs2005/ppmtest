"""
Markdown导出器
"""

from typing import List, Dict, Any
from datetime import datetime

from .base_exporter import BaseExporter
from ..models import KnowledgeEntry


class MarkdownExporter(BaseExporter):
    """Markdown导出器"""
    
    def export(self, entries: List[KnowledgeEntry], metadata: Dict[str, Any] = None) -> str:
        """
        导出为Markdown格式
        
        Args:
            entries: 知识条目列表
            metadata: 元数据
            
        Returns:
            str: Markdown格式的导出内容
        """
        # 构建导出数据
        export_metadata = self._build_metadata(entries, metadata)
        
        # 生成Markdown内容
        md_content = self._generate_header(export_metadata)
        md_content += self._generate_table_of_contents(entries)
        md_content += self._generate_statistics(entries)
        md_content += self._generate_entries(entries)
        md_content += self._generate_footer(export_metadata)
        
        return md_content
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.md'
    
    def get_content_type(self) -> str:
        """获取内容类型"""
        return 'text/markdown'
    
    def _generate_header(self, metadata: Dict[str, Any]) -> str:
        """
        生成文档头部
        
        Args:
            metadata: 元数据
            
        Returns:
            str: Markdown头部
        """
        header = "# 知识库导出\n\n"
        header += f"**导出时间**: {datetime.fromisoformat(metadata['export_time']).strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"**导出工具**: {metadata['exporter']}\n"
        header += f"**总条目数**: {metadata['total_entries']}\n"
        
        if 'query' in metadata:
            header += f"**搜索查询**: {metadata['query']}\n"
        
        if 'filters' in metadata:
            header += f"**过滤条件**: {metadata['filters']}\n"
        
        header += "\n---\n\n"
        
        return header
    
    def _generate_table_of_contents(self, entries: List[KnowledgeEntry]) -> str:
        """
        生成目录
        
        Args:
            entries: 知识条目列表
            
        Returns:
            str: Markdown目录
        """
        toc = "## 目录\n\n"
        
        # 按类型分组
        from collections import defaultdict
        type_groups = defaultdict(list)
        
        for entry in entries:
            type_groups[entry.knowledge_type].append(entry)
        
        # 生成目录
        for knowledge_type, type_entries in type_groups.items():
            toc += f"- **{knowledge_type}** ({len(type_entries)})\n"
            for entry in type_entries[:10]:  # 最多显示10个
                toc += f"  - [{entry.title}](#entry-{entry.id})\n"
            if len(type_entries) > 10:
                toc += f"  - ...还有 {len(type_entries) - 10} 个条目\n"
            toc += "\n"
        
        return toc + "---\n\n"
    
    def _generate_statistics(self, entries: List[KnowledgeEntry]) -> str:
        """
        生成统计信息
        
        Args:
            entries: 知识条目列表
            
        Returns:
            str: Markdown统计信息
        """
        from collections import defaultdict
        
        stats = "## 统计信息\n\n"
        
        # 按类型统计
        type_counts = defaultdict(int)
        importance_counts = defaultdict(int)
        tag_counts = defaultdict(int)
        
        for entry in entries:
            type_counts[entry.knowledge_type] += 1
            importance_counts[entry.importance] += 1
            for tag in entry.tags:
                tag_counts[tag.name] += 1
        
        # 类型统计
        stats += "### 按类型统计\n\n"
        for knowledge_type, count in sorted(type_counts.items()):
            stats += f"- **{knowledge_type}**: {count} 个条目\n"
        stats += "\n"
        
        # 重要性统计
        stats += "### 按重要性统计\n\n"
        for importance in range(1, 6):
            count = importance_counts.get(importance, 0)
            stars = "⭐" * importance
            stats += f"- **{stars} (级别 {importance})**: {count} 个条目\n"
        stats += "\n"
        
        # 热门标签
        stats += "### 热门标签\n\n"
        popular_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]
        for tag, count in popular_tags:
            stats += f"- **{tag}**: {count} 个条目\n"
        stats += "\n"
        
        return stats + "---\n\n"
    
    def _generate_entries(self, entries: List[KnowledgeEntry]) -> str:
        """
        生成知识条目内容
        
        Args:
            entries: 知识条目列表
            
        Returns:
            str: Markdown条目内容
        """
        content = "## 知识条目\n\n"
        
        # 按类型分组
        from collections import defaultdict
        type_groups = defaultdict(list)
        
        for entry in entries:
            type_groups[entry.knowledge_type].append(entry)
        
        # 按类型生成内容
        for knowledge_type, type_entries in sorted(type_groups.items()):
            content += f"### {knowledge_type}\n\n"
            
            # 按重要性排序
            type_entries.sort(key=lambda x: x.importance, reverse=True)
            
            for entry in type_entries:
                content += self._generate_single_entry(entry)
                content += "\n---\n\n"
        
        return content
    
    def _generate_single_entry(self, entry: KnowledgeEntry) -> str:
        """
        生成单个知识条目
        
        Args:
            entry: 知识条目
            
        Returns:
            str: Markdown条目
        """
        entry_content = f'<a id="entry-{entry.id}"></a>\n'
        entry_content += f"#### {entry.title}\n\n"
        
        # 元信息
        entry_content += f"**重要性**: {'⭐' * entry.importance}\n"
        entry_content += f"**类型**: {entry.knowledge_type}\n"
        entry_content += f"**创建时间**: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else 'N/A'}\n"
        
        # 标签
        if entry.tags:
            tags = [f"`{tag.name}`" for tag in entry.tags]
            entry_content += f"**标签**: {' '.join(tags)}\n"
        
        # 来源信息
        if entry.analysis and entry.analysis.video:
            entry_content += f"**来源视频**: [{entry.analysis.video.title}](https://www.bilibili.com/video/{entry.analysis.video.bvid})\n"
        
        entry_content += "\n"
        
        # 内容
        entry_content += "##### 内容\n\n"
        entry_content += f"{entry.content}\n\n"
        
        # 源分析总结
        if entry.analysis and entry.analysis.summary:
            entry_content += "##### 相关分析\n\n"
            entry_content += f"> {entry.analysis.summary}\n\n"
        
        return entry_content
    
    def _generate_footer(self, metadata: Dict[str, Any]) -> str:
        """
        生成文档尾部
        
        Args:
            metadata: 元数据
            
        Returns:
            str: Markdown尾部
        """
        footer = "---\n\n"
        footer += "## 导出说明\n\n"
        footer += "本文档由Bilibili视频分析系统自动生成，包含所有匹配条件的知识条目。\n\n"
        footer += f"**导出时间**: {datetime.fromisoformat(metadata['export_time']).strftime('%Y-%m-%d %H:%M:%S')}\n"
        footer += f"**导出工具**: {metadata['exporter']}\n"
        
        return footer