"""
知识库管理模块验证脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from bilibili_analyzer.models import db
from bilibili_analyzer.managers import KnowledgeManager
from bilibili_analyzer.services.search import SearchService
from bilibili_analyzer.exporters import JsonExporter, MarkdownExporter, CsvExporter
from bilibili_analyzer.analyzers.content_analyzer import AnalysisResult
import json
import time


def create_test_app():
    """创建测试应用"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app


def test_knowledge_manager():
    """测试知识库管理器"""
    print("=== 测试知识库管理器 ===")
    
    app = create_test_app()
    
    with app.app_context():
        # 创建管理器
        knowledge_manager = KnowledgeManager()
        
        # 创建测试分析结果
        analysis_result = AnalysisResult(
            summary="这是一个关于Python编程的测试总结",
            key_points=["Python是一种高级编程语言", "Python具有简洁的语法", "Python有丰富的库支持"],
            categories=["技术", "编程", "教育"],
            tags=["Python", "编程", "软件开发"],
            knowledge_entries=[
                {
                    "title": "Python编程基础",
                    "content": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。它具有简洁易读的语法，支持多种编程范式。",
                    "type": "concept",
                    "importance": 5,
                    "tags": ["Python", "编程", "基础"]
                },
                {
                    "title": "Python语法特点",
                    "content": "Python的语法简洁明了，使用缩进来表示代码块。变量不需要声明类型，支持动态类型。",
                    "type": "fact",
                    "importance": 4,
                    "tags": ["Python", "语法", "特点"]
                },
                {
                    "title": "Python开发环境搭建",
                    "content": "1. 安装Python解释器 2. 安装IDE（如PyCharm、VSCode）3. 配置虚拟环境 4. 安装必要的包",
                    "type": "method",
                    "importance": 3,
                    "tags": ["Python", "环境", "开发"]
                }
            ],
            total_tokens=150,
            total_cost=0.02,
            analysis_time=2.5,
            model_used="gpt-3.5-turbo",
            chunk_count=1
        )
        
        # 测试保存分析结果
        print("1. 测试保存分析结果...")
        try:
            analysis = knowledge_manager.save_analysis_result(analysis_result)
            print(f"✓ 保存成功，分析ID: {analysis.id}")
        except Exception as e:
            print(f"✗ 保存失败: {e}")
            return False
        
        # 测试搜索功能
        print("2. 测试搜索功能...")
        try:
            results = knowledge_manager.search_knowledge("Python")
            print(f"✓ 搜索成功，找到 {len(results)} 条结果")
            if results:
                print(f"  第一条结果: {results[0]['title']}")
        except Exception as e:
            print(f"✗ 搜索失败: {e}")
            return False
        
        # 测试标签搜索
        print("3. 测试标签搜索...")
        try:
            results = knowledge_manager.get_knowledge_by_tags(["Python"])
            print(f"✓ 标签搜索成功，找到 {len(results)} 条结果")
        except Exception as e:
            print(f"✗ 标签搜索失败: {e}")
            return False
        
        # 测试导出功能
        print("4. 测试导出功能...")
        try:
            # JSON导出
            json_export = knowledge_manager.export_knowledge("json")
            print(f"✓ JSON导出成功，数据大小: {len(json_export)} 字符")
            
            # Markdown导出
            md_export = knowledge_manager.export_knowledge("markdown")
            print(f"✓ Markdown导出成功，数据大小: {len(md_export)} 字符")
            
            # CSV导出
            csv_export = knowledge_manager.export_knowledge("csv")
            print(f"✓ CSV导出成功，数据大小: {len(csv_export)} 字符")
        except Exception as e:
            print(f"✗ 导出失败: {e}")
            return False
        
        # 测试统计功能
        print("5. 测试统计功能...")
        try:
            stats = knowledge_manager.get_knowledge_stats()
            print(f"✓ 统计功能成功")
            print(f"  总条目数: {stats.get('total_entries', 0)}")
            print(f"  总标签数: {stats.get('total_tags', 0)}")
            print(f"  总分析数: {stats.get('total_analyses', 0)}")
        except Exception as e:
            print(f"✗ 统计失败: {e}")
            return False
        
        return True


def test_search_service():
    """测试搜索服务"""
    print("\n=== 测试搜索服务 ===")
    
    app = create_test_app()
    
    with app.app_context():
        search_service = SearchService()
        
        # 测试搜索建议
        print("1. 测试搜索建议...")
        try:
            suggestions = search_service.get_search_suggestions("Python")
            print(f"✓ 搜索建议成功，找到 {len(suggestions)} 条建议")
        except Exception as e:
            print(f"✗ 搜索建议失败: {e}")
            return False
        
        # 测试按类型搜索
        print("2. 测试按类型搜索...")
        try:
            results = search_service.search_by_type("concept")
            print(f"✓ 按类型搜索成功，找到 {len(results)} 条结果")
        except Exception as e:
            print(f"✗ 按类型搜索失败: {e}")
            return False
        
        # 测试搜索统计
        print("3. 测试搜索统计...")
        try:
            stats = search_service.get_search_stats()
            print(f"✓ 搜索统计成功")
            print(f"  总条目数: {stats.get('total_entries', 0)}")
            print(f"  总标签数: {stats.get('total_tags', 0)}")
            print(f"  FTS启用: {stats.get('fts_enabled', False)}")
        except Exception as e:
            print(f"✗ 搜索统计失败: {e}")
            return False
        
        return True


def test_exporters():
    """测试导出器"""
    print("\n=== 测试导出器 ===")
    
    app = create_test_app()
    
    with app.app_context():
        from bilibili_analyzer.models import KnowledgeEntry
        
        # 获取测试数据
        entries = KnowledgeEntry.query.all()
        
        if not entries:
            print("✗ 没有找到测试数据")
            return False
        
        # 测试JSON导出器
        print("1. 测试JSON导出器...")
        try:
            json_exporter = JsonExporter()
            json_data = json_exporter.export(entries)
            print(f"✓ JSON导出成功，数据大小: {len(json_data)} 字符")
            
            # 验证JSON格式
            parsed_data = json.loads(json_data)
            assert 'entries' in parsed_data
            assert 'statistics' in parsed_data
            print("✓ JSON格式验证成功")
        except Exception as e:
            print(f"✗ JSON导出失败: {e}")
            return False
        
        # 测试Markdown导出器
        print("2. 测试Markdown导出器...")
        try:
            md_exporter = MarkdownExporter()
            md_data = md_exporter.export(entries)
            print(f"✓ Markdown导出成功，数据大小: {len(md_data)} 字符")
            
            # 验证Markdown内容
            assert '# 知识库导出' in md_data
            assert '## 统计信息' in md_data
            print("✓ Markdown格式验证成功")
        except Exception as e:
            print(f"✗ Markdown导出失败: {e}")
            return False
        
        # 测试CSV导出器
        print("3. 测试CSV导出器...")
        try:
            csv_exporter = CsvExporter()
            csv_data = csv_exporter.export(entries)
            print(f"✓ CSV导出成功，数据大小: {len(csv_data)} 字符")
            
            # 验证CSV内容
            assert 'ID,标题,内容' in csv_data
            print("✓ CSV格式验证成功")
        except Exception as e:
            print(f"✗ CSV导出失败: {e}")
            return False
        
        return True


def test_performance():
    """测试性能"""
    print("\n=== 测试性能 ===")
    
    app = create_test_app()
    
    with app.app_context():
        knowledge_manager = KnowledgeManager()
        
        # 测试搜索性能
        print("1. 测试搜索性能...")
        try:
            queries = ["Python", "编程", "概念", "方法", "事实"]
            total_time = 0
            
            for query in queries:
                start_time = time.time()
                results = knowledge_manager.search_knowledge(query)
                end_time = time.time()
                search_time = end_time - start_time
                total_time += search_time
                
                print(f"  查询 '{query}': {search_time:.3f}秒 ({len(results)} 条结果)")
                
                # 验证性能要求
                if search_time > 2.0:
                    print(f"✗ 查询 '{query}' 耗时过长: {search_time:.3f}秒")
                    return False
            
            avg_time = total_time / len(queries)
            print(f"平均搜索时间: {avg_time:.3f}秒")
            
            if avg_time > 1.0:
                print(f"✗ 平均搜索时间过长: {avg_time:.3f}秒")
                return False
            
            print("✓ 搜索性能测试通过")
        except Exception as e:
            print(f"✗ 搜索性能测试失败: {e}")
            return False
        
        # 测试导出性能
        print("2. 测试导出性能...")
        try:
            formats = ["json", "markdown", "csv"]
            
            for format_type in formats:
                start_time = time.time()
                exported_data = knowledge_manager.export_knowledge(format_type)
                end_time = time.time()
                export_time = end_time - start_time
                
                print(f"  导出 {format_type}: {export_time:.3f}秒 ({len(exported_data)} 字符)")
                
                # 验证性能要求
                if export_time > 5.0:
                    print(f"✗ 导出 {format_type} 耗时过长: {export_time:.3f}秒")
                    return False
            
            print("✓ 导出性能测试通过")
        except Exception as e:
            print(f"✗ 导出性能测试失败: {e}")
            return False
        
        return True


def main():
    """主函数"""
    print("开始验证知识库管理模块...")
    
    # 测试知识库管理器
    if not test_knowledge_manager():
        print("✗ 知识库管理器测试失败")
        return False
    
    # 测试搜索服务
    if not test_search_service():
        print("✗ 搜索服务测试失败")
        return False
    
    # 测试导出器
    if not test_exporters():
        print("✗ 导出器测试失败")
        return False
    
    # 测试性能
    if not test_performance():
        print("✗ 性能测试失败")
        return False
    
    print("\n🎉 所有测试通过！知识库管理模块验证成功。")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)