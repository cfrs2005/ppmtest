"""
CSV导出器
"""

import csv
import io
from typing import List, Dict, Any

from .base_exporter import BaseExporter
from ..models import KnowledgeEntry


class CsvExporter(BaseExporter):
    """CSV导出器"""
    
    def export(self, entries: List[KnowledgeEntry], metadata: Dict[str, Any] = None) -> str:
        """
        导出为CSV格式
        
        Args:
            entries: 知识条目列表
            metadata: 元数据
            
        Returns:
            str: CSV格式的导出内容
        """
        # 创建CSV写入器
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入元数据注释
        if metadata:
            writer.writerow([f"# Exported by: {metadata.get('exporter', 'Unknown')}"])
            writer.writerow([f"# Export time: {metadata.get('export_time', 'Unknown')}"])
            writer.writerow([f"# Total entries: {metadata.get('total_entries', 0)}"])
            if 'query' in metadata:
                writer.writerow([f"# Search query: {metadata['query']}"])
            writer.writerow([])  # 空行
        
        # 写入表头
        writer.writerow([
            'ID', '标题', '内容', '知识类型', '重要性', '创建时间', '更新时间',
            '标签', '视频ID', '视频标题', 'BV号', '分析总结', '源时间戳'
        ])
        
        # 写入数据
        for entry in entries:
            writer.writerow([
                entry.id,
                entry.title,
                self._clean_csv_field(entry.content),
                entry.knowledge_type,
                entry.importance,
                entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else '',
                entry.updated_at.strftime('%Y-%m-%d %H:%M:%S') if entry.updated_at else '',
                '|'.join([tag.name for tag in entry.tags]),
                entry.analysis.video.id if entry.analysis and entry.analysis.video else '',
                entry.analysis.video.title if entry.analysis and entry.analysis.video else '',
                entry.analysis.video.bvid if entry.analysis and entry.analysis.video else '',
                self._clean_csv_field(entry.analysis.summary if entry.analysis else ''),
                entry.source_timestamp or ''
            ])
        
        return output.getvalue()
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.csv'
    
    def get_content_type(self) -> str:
        """获取内容类型"""
        return 'text/csv'
    
    def _clean_csv_field(self, field: str) -> str:
        """
        清理CSV字段内容
        
        Args:
            field: 字段内容
            
        Returns:
            str: 清理后的字段内容
        """
        if not field:
            return ''
        
        # 替换换行符和特殊字符
        cleaned = str(field).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 移除多余的空格
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def export_separate_files(self, entries: List[KnowledgeEntry], metadata: Dict[str, Any] = None) -> Dict[str, str]:
        """
        导出为多个分离的CSV文件
        
        Args:
            entries: 知识条目列表
            metadata: 元数据
            
        Returns:
            Dict[str, str]: 文件名到内容的映射
        """
        from collections import defaultdict
        
        # 按类型分组
        type_groups = defaultdict(list)
        for entry in entries:
            type_groups[entry.knowledge_type].append(entry)
        
        files = {}
        
        # 为每种类型创建单独的文件
        for knowledge_type, type_entries in type_groups.items():
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                'ID', '标题', '内容', '重要性', '创建时间', '更新时间',
                '标签', '视频标题', 'BV号', '分析总结'
            ])
            
            # 写入数据
            for entry in type_entries:
                writer.writerow([
                    entry.id,
                    entry.title,
                    self._clean_csv_field(entry.content),
                    entry.importance,
                    entry.created_at.strftime('%Y-%m-%d %H:%M:%S') if entry.created_at else '',
                    entry.updated_at.strftime('%Y-%m-%d %H:%M:%S') if entry.updated_at else '',
                    '|'.join([tag.name for tag in entry.tags]),
                    entry.analysis.video.title if entry.analysis and entry.analysis.video else '',
                    entry.analysis.video.bvid if entry.analysis and entry.analysis.video else '',
                    self._clean_csv_field(entry.analysis.summary if entry.analysis else '')
                ])
            
            filename = f"knowledge_entries_{knowledge_type.lower()}.csv"
            files[filename] = output.getvalue()
        
        return files
    
    def export_summary_report(self, entries: List[KnowledgeEntry], metadata: Dict[str, Any] = None) -> str:
        """
        导出汇总报告
        
        Args:
            entries: 知识条目列表
            metadata: 元数据
            
        Returns:
            str: CSV格式的汇总报告
        """
        from collections import defaultdict
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入报告头部
        writer.writerow(['知识库汇总报告'])
        writer.writerow([])
        
        # 基本统计
        writer.writerow(['基本统计'])
        writer.writerow(['总条目数', len(entries)])
        writer.writerow([])
        
        # 按类型统计
        type_counts = defaultdict(int)
        for entry in entries:
            type_counts[entry.knowledge_type] += 1
        
        writer.writerow(['按类型统计'])
        writer.writerow(['类型', '数量', '占比'])
        for knowledge_type, count in sorted(type_counts.items()):
            percentage = (count / len(entries)) * 100 if entries else 0
            writer.writerow([knowledge_type, count, f'{percentage:.1f}%'])
        writer.writerow([])
        
        # 按重要性统计
        importance_counts = defaultdict(int)
        for entry in entries:
            importance_counts[entry.importance] += 1
        
        writer.writerow(['按重要性统计'])
        writer.writerow(['重要性', '数量', '占比'])
        for importance in range(1, 6):
            count = importance_counts.get(importance, 0)
            percentage = (count / len(entries)) * 100 if entries else 0
            writer.writerow([f"级别 {importance}", count, f'{percentage:.1f}%'])
        writer.writerow([])
        
        # 标签统计
        tag_counts = defaultdict(int)
        for entry in entries:
            for tag in entry.tags:
                tag_counts[tag.name] += 1
        
        writer.writerow(['热门标签'])
        writer.writerow(['标签', '出现次数'])
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            writer.writerow([tag, count])
        
        return output.getvalue()