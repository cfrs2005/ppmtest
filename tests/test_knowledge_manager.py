"""
知识库管理模块测试
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch

from bilibili_analyzer.models import db, KnowledgeEntry, Analysis, Video, Subtitle, Tag
from bilibili_analyzer.managers import KnowledgeManager
from bilibili_analyzer.services.search import SearchService
from bilibili_analyzer.exporters import JsonExporter, MarkdownExporter, CsvExporter
from bilibili_analyzer.analyzers.content_analyzer import AnalysisResult


class TestKnowledgeManager:
    """知识库管理器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.knowledge_manager = KnowledgeManager()
        self.search_service = SearchService()
    
    def test_save_analysis_result(self, app):
        """测试保存分析结果"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            # 创建分析结果
            analysis_result = AnalysisResult(
                summary='测试总结',
                key_points=['关键点1', '关键点2'],
                categories=['技术', '教育'],
                tags=['Python', '编程'],
                knowledge_entries=[
                    {
                        'title': '测试知识条目',
                        'content': '测试内容',
                        'type': 'concept',
                        'importance': 3,
                        'tags': ['Python', '编程']
                    }
                ],
                total_tokens=100,
                total_cost=0.01,
                analysis_time=1.5,
                model_used='gpt-3.5-turbo',
                chunk_count=1
            )
            
            # 保存分析结果
            analysis = self.knowledge_manager.save_analysis_result(analysis_result)
            
            # 验证结果
            assert analysis.id is not None
            assert analysis.summary == '测试总结'
            assert analysis.key_points is not None
            
            # 验证知识条目
            knowledge_entries = KnowledgeEntry.query.filter_by(analysis_id=analysis.id).all()
            assert len(knowledge_entries) == 1
            assert knowledge_entries[0].title == '测试知识条目'
    
    def test_search_knowledge(self, app):
        """测试搜索知识条目"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            # 创建知识条目
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            
            # 添加标签
            tag1 = Tag(name='Python')
            tag2 = Tag(name='编程')
            db.session.add_all([tag1, tag2])
            db.session.flush()
            
            knowledge_entry.tags.extend([tag1, tag2])
            db.session.commit()
            
            # 测试搜索
            results = self.knowledge_manager.search_knowledge('Python')
            assert len(results) > 0
            assert 'Python' in results[0]['title']
    
    def test_get_knowledge_by_tags(self, app):
        """测试根据标签获取知识条目"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            # 创建知识条目
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            
            # 添加标签
            tag1 = Tag(name='Python')
            tag2 = Tag(name='编程')
            db.session.add_all([tag1, tag2])
            db.session.flush()
            
            knowledge_entry.tags.extend([tag1, tag2])
            db.session.commit()
            
            # 测试根据标签获取
            results = self.knowledge_manager.get_knowledge_by_tags(['Python'])
            assert len(results) > 0
            assert 'Python' in results[0]['title']
    
    def test_update_knowledge_entry(self, app):
        """测试更新知识条目"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='原标题',
                content='原内容',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 更新知识条目
            updates = {
                'title': '新标题',
                'content': '新内容',
                'importance': 4
            }
            
            updated_entry = self.knowledge_manager.update_knowledge_entry(knowledge_entry.id, updates)
            
            # 验证更新
            assert updated_entry['title'] == '新标题'
            assert updated_entry['content'] == '新内容'
            assert updated_entry['importance'] == 4
    
    def test_delete_knowledge_entry(self, app):
        """测试删除知识条目"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='测试条目',
                content='测试内容',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 删除知识条目
            result = self.knowledge_manager.delete_knowledge_entry(knowledge_entry.id)
            
            # 验证删除
            assert result is True
            deleted_entry = KnowledgeEntry.query.get(knowledge_entry.id)
            assert deleted_entry is None
    
    def test_export_knowledge(self, app):
        """测试导出知识库"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 测试JSON导出
            json_export = self.knowledge_manager.export_knowledge('json')
            assert len(json_export) > 0
            
            # 验证JSON格式
            data = json.loads(json_export)
            assert 'entries' in data
            assert len(data['entries']) > 0
            
            # 测试Markdown导出
            md_export = self.knowledge_manager.export_knowledge('markdown')
            assert len(md_export) > 0
            assert '# 知识库导出' in md_export
            
            # 测试CSV导出
            csv_export = self.knowledge_manager.export_knowledge('csv')
            assert len(csv_export) > 0
            assert 'ID,标题,内容' in csv_export
    
    def test_get_knowledge_stats(self, app):
        """测试获取知识库统计"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 获取统计信息
            stats = self.knowledge_manager.get_knowledge_stats()
            
            # 验证统计信息
            assert 'total_entries' in stats
            assert 'total_tags' in stats
            assert 'total_analyses' in stats
            assert 'type_distribution' in stats
            assert 'importance_distribution' in stats
            assert stats['total_entries'] >= 1


class TestSearchService:
    """搜索服务测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.search_service = SearchService()
    
    def test_search_functionality(self, app):
        """测试搜索功能"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            
            # 添加标签
            tag1 = Tag(name='Python')
            tag2 = Tag(name='编程')
            db.session.add_all([tag1, tag2])
            db.session.flush()
            
            knowledge_entry.tags.extend([tag1, tag2])
            db.session.commit()
            
            # 测试全文搜索
            results = self.search_service.search('Python')
            assert len(results) > 0
            
            # 测试标签搜索
            results = self.search_service.search('Python', search_type='tags')
            assert len(results) > 0
            
            # 测试组合搜索
            results = self.search_service.search('Python', search_type='combined')
            assert len(results) > 0
    
    def test_search_by_type(self, app):
        """测试按类型搜索"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 测试按类型搜索
            results = self.search_service.search_by_type('concept')
            assert len(results) > 0
            
            # 测试带查询的类型搜索
            results = self.search_service.search_by_type('concept', 'Python')
            assert len(results) > 0


class TestExporters:
    """导出器测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.json_exporter = JsonExporter()
        self.markdown_exporter = MarkdownExporter()
        self.csv_exporter = CsvExporter()
    
    def test_json_exporter(self, app):
        """测试JSON导出器"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 测试导出
            entries = KnowledgeEntry.query.all()
            exported_data = self.json_exporter.export(entries)
            
            # 验证导出结果
            assert len(exported_data) > 0
            data = json.loads(exported_data)
            assert 'entries' in data
            assert 'statistics' in data
            assert len(data['entries']) > 0
            
            # 验证文件扩展名
            assert self.json_exporter.get_file_extension() == '.json'
            assert self.json_exporter.get_content_type() == 'application/json'
    
    def test_markdown_exporter(self, app):
        """测试Markdown导出器"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 测试导出
            entries = KnowledgeEntry.query.all()
            exported_data = self.markdown_exporter.export(entries)
            
            # 验证导出结果
            assert len(exported_data) > 0
            assert '# 知识库导出' in exported_data
            assert '## 统计信息' in exported_data
            assert '## 知识条目' in exported_data
            
            # 验证文件扩展名
            assert self.markdown_exporter.get_file_extension() == '.md'
            assert self.markdown_exporter.get_content_type() == 'text/markdown'
    
    def test_csv_exporter(self, app):
        """测试CSV导出器"""
        with app.app_context():
            # 创建测试数据
            video = Video(
                bvid='test_bvid',
                title='测试视频',
                author='测试作者'
            )
            db.session.add(video)
            db.session.flush()
            
            subtitle = Subtitle(
                video_id=video.id,
                language='zh',
                format='json',
                content='{"body": [{"text": "测试内容"}]}'
            )
            db.session.add(subtitle)
            db.session.flush()
            
            analysis = Analysis(
                video_id=video.id,
                subtitle_id=subtitle.id,
                summary='测试总结',
                key_points=json.dumps(['关键点1', '关键点2'], ensure_ascii=False),
                categories=json.dumps(['技术', '教育'], ensure_ascii=False),
                tags=json.dumps(['Python', '编程'], ensure_ascii=False),
                analysis_time=1.5,
                model_used='gpt-3.5-turbo'
            )
            db.session.add(analysis)
            db.session.flush()
            
            knowledge_entry = KnowledgeEntry(
                analysis_id=analysis.id,
                title='Python编程',
                content='Python是一种高级编程语言',
                knowledge_type='concept',
                importance=3
            )
            db.session.add(knowledge_entry)
            db.session.commit()
            
            # 测试导出
            entries = KnowledgeEntry.query.all()
            exported_data = self.csv_exporter.export(entries)
            
            # 验证导出结果
            assert len(exported_data) > 0
            assert 'ID,标题,内容' in exported_data
            assert 'Python编程' in exported_data
            
            # 验证文件扩展名
            assert self.csv_exporter.get_file_extension() == '.csv'
            assert self.csv_exporter.get_content_type() == 'text/csv'
            
            # 测试汇总报告
            summary_report = self.csv_exporter.export_summary_report(entries)
            assert len(summary_report) > 0
            assert '知识库汇总报告' in summary_report


if __name__ == '__main__':
    pytest.main([__file__])