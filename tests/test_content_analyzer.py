"""
大模型内容分析模块测试
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from bilibili_analyzer.services import (
    LLMServiceManager, 
    ModelConfig, 
    LLMProvider, 
    ModelType,
    LLMMessage,
    AnalysisService
)
from bilibili_analyzer.analyzers import ContentAnalyzer, AnalysisResult
from bilibili_analyzer.cache import CacheManager
from bilibili_analyzer.utils import TokenManager


class TestLLMService:
    """LLM服务测试"""
    
    def test_llm_service_manager(self):
        """测试LLM服务管理器"""
        manager = LLMServiceManager()
        
        # 测试添加服务
        config = ModelConfig(
            provider=LLMProvider.OPENAI,
            model=ModelType.GPT_3_5_TURBO,
            max_tokens=1000
        )
        
        # 模拟服务
        mock_service = Mock()
        manager.add_service("test", mock_service, is_default=True)
        
        # 测试获取服务
        service = manager.get_service("test")
        assert service == mock_service
        
        # 测试默认服务
        default_service = manager.get_service()
        assert default_service == mock_service
        
        # 测试可用服务列表
        services = manager.get_available_services()
        assert "test" in services
    
    def test_model_config(self):
        """测试模型配置"""
        config = ModelConfig(
            provider=LLMProvider.OPENAI,
            model=ModelType.GPT_3_5_TURBO,
            max_tokens=2000,
            temperature=0.7
        )
        
        assert config.provider == LLMProvider.OPENAI
        assert config.model == ModelType.GPT_3_5_TURBO
        assert config.max_tokens == 2000
        assert config.temperature == 0.7
    
    def test_llm_message(self):
        """测试LLM消息"""
        message = LLMMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"


class TestTextPreprocessor:
    """文本预处理器测试"""
    
    def setup_method(self):
        from bilibili_analyzer.analyzers.text_preprocessor import TextPreprocessor
        self.preprocessor = TextPreprocessor()
    
    def test_clean_text(self):
        """测试文本清理"""
        text = """
        这是一个测试
        
        666
        哈哈哈哈
        ！！！
        
        正常内容
        """
        
        cleaned = self.preprocessor.clean_text(text)
        assert "666" not in cleaned
        assert "哈哈哈" not in cleaned
        assert "！！！" not in cleaned
        assert "正常内容" in cleaned
    
    def test_merge_lines(self):
        """测试行合并"""
        text = "这是第一行\n这是第二行"
        merged = self.preprocessor.merge_lines(text)
        assert "第一行 第二行" in merged
    
    def test_extract_sentences(self):
        """测试句子提取"""
        text = "这是第一句。这是第二句！这是第三句？"
        sentences = self.preprocessor.extract_sentences(text)
        assert len(sentences) == 3
        assert "这是第一句" in sentences[0]
        assert "这是第二句" in sentences[1]
        assert "这是第三句" in sentences[2]
    
    def test_get_text_stats(self):
        """测试文本统计"""
        text = "这是一个测试文本。This is an English sentence."
        stats = self.preprocessor.get_text_stats(text)
        
        assert 'total_chars' in stats
        assert 'total_words' in stats
        assert 'total_sentences' in stats
        assert 'chinese_chars' in stats
        assert 'english_words' in stats
        assert 'language_ratio' in stats
        
        assert stats['chinese_chars'] > 0
        assert stats['english_words'] > 0


class TestChunkProcessor:
    """分块处理器测试"""
    
    def setup_method(self):
        from bilibili_analyzer.analyzers.chunk_processor import ChunkProcessor, ChunkConfig
        self.processor = ChunkProcessor(ChunkConfig(max_tokens=100))
    
    def test_chunk_text(self):
        """测试文本分块"""
        text = "这是一个测试句子。" * 20  # 创建长文本
        chunks = self.processor.chunk_text(text)
        
        assert len(chunks) > 1
        assert all(chunk.content for chunk in chunks)
        assert all(chunk.start_index < chunk.end_index for chunk in chunks)
    
    def test_count_tokens(self):
        """测试Token计数"""
        text = "这是一个测试文本"
        tokens = self.processor.count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_optimize_chunks(self):
        """测试分块优化"""
        from bilibili_analyzer.analyzers.chunk_processor import TextChunk
        
        # 创建包含短chunk的列表
        chunks = [
            TextChunk("短内容", 0, 3),
            TextChunk("这是一个较长的内容，应该保留", 3, 20),
            TextChunk("另一个短内容", 20, 26),
        ]
        
        optimized = self.processor.optimize_chunks(chunks)
        
        # 短chunk应该被合并或删除
        assert len(optimized) <= len(chunks)
        assert all(self.processor.count_tokens(chunk.content) >= 10 for chunk in optimized)


class TestCacheManager:
    """缓存管理器测试"""
    
    def setup_method(self):
        self.cache_manager = CacheManager()
    
    def test_basic_cache_operations(self):
        """测试基本缓存操作"""
        cache = self.cache_manager.get_memory_cache()
        
        # 测试设置和获取
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        assert value == "test_value"
        
        # 测试删除
        result = cache.delete("test_key")
        assert result == True
        
        # 测试获取不存在的键
        value = cache.get("test_key")
        assert value is None
    
    def test_cache_stats(self):
        """测试缓存统计"""
        cache = self.cache_manager.get_memory_cache()
        
        # 执行一些操作
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent_key")
        
        stats = cache.get_stats()
        assert 'hits' in stats
        assert 'misses' in stats
        assert 'hit_rate' in stats
        assert stats['hits'] == 1
        assert stats['misses'] == 1


class TestTokenManager:
    """Token管理器测试"""
    
    def setup_method(self):
        self.token_manager = TokenManager(
            daily_token_limit=1000,
            daily_cost_limit=1.0
        )
    
    def test_record_usage(self):
        """测试使用记录"""
        self.token_manager.record_usage(
            tokens=100,
            cost=0.1,
            model="gpt-3.5-turbo",
            task_type="test"
        )
        
        stats = self.token_manager.get_usage_stats()
        assert stats.total_tokens == 100
        assert stats.total_cost == 0.1
    
    def test_check_limit(self):
        """测试限制检查"""
        # 测试正常情况
        result = self.token_manager.check_limit(100, 0.1)
        assert result == True
        
        # 测试超限情况
        result = self.token_manager.check_limit(2000, 2.0)
        assert result == False
    
    def test_estimate_cost(self):
        """测试成本估算"""
        cost = self.token_manager.estimate_cost(1000, "gpt-3.5-turbo")
        assert cost > 0
        assert isinstance(cost, float)


class TestContentAnalyzer:
    """内容分析器测试"""
    
    def setup_method(self):
        self.llm_manager = LLMServiceManager()
        self.analyzer = ContentAnalyzer(self.llm_manager)
    
    @pytest.mark.asyncio
    async def test_analyze_subtitle_mock(self):
        """测试字幕分析（模拟）"""
        # 模拟字幕内容
        subtitle_content = json.dumps({
            "body": [
                {"content": "这是第一句字幕"},
                {"content": "这是第二句字幕"},
                {"content": "这是第三句字幕"}
            ]
        })
        
        # 模拟LLM响应
        mock_response = Mock()
        mock_response.content = json.dumps({
            "summary": "这是一个测试总结",
            "key_points": ["关键点1", "关键点2"],
            "categories": ["教育", "技术"],
            "tags": ["测试", "字幕"],
            "knowledge_entries": []
        })
        mock_response.tokens_used = 100
        mock_response.cost = 0.01
        mock_response.latency = 1.0
        
        with patch.object(self.llm_manager, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            result = await self.analyzer.analyze_subtitle(subtitle_content)
            
            assert isinstance(result, AnalysisResult)
            assert result.summary == "这是一个测试总结"
            assert len(result.key_points) == 2
            assert len(result.categories) == 2
            assert result.total_tokens == 100
            assert result.total_cost == 0.01
    
    @pytest.mark.asyncio
    async def test_generate_summary_mock(self):
        """测试总结生成（模拟）"""
        content = "这是一个测试内容"
        mock_response = Mock()
        mock_response.content = "这是生成的总结"
        
        with patch.object(self.llm_manager, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            summary = await self.analyzer.generate_summary(content)
            assert summary == "这是生成的总结"
    
    @pytest.mark.asyncio
    async def test_extract_key_points_mock(self):
        """测试关键点提取（模拟）"""
        content = "这是一个测试内容"
        mock_response = Mock()
        mock_response.content = json.dumps({
            "key_points": ["关键点1", "关键点2", "关键点3"]
        })
        
        with patch.object(self.llm_manager, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            key_points = await self.analyzer.extract_key_points(content)
            assert len(key_points) == 3
            assert "关键点1" in key_points


class TestAnalysisService:
    """分析服务测试"""
    
    def setup_method(self):
        self.service = AnalysisService()
    
    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service.llm_manager is not None
        assert self.service.cache_manager is not None
        assert self.service.token_manager is not None
        assert self.service.analyzer is not None
    
    def test_get_analysis_stats(self):
        """测试获取分析统计"""
        stats = self.service.get_analysis_stats()
        assert 'cache_stats' in stats
        assert 'token_stats' in stats
        assert 'limit_status' in stats
        assert 'available_services' in stats
    
    def test_get_cost_analysis(self):
        """测试获取成本分析"""
        analysis = self.service.get_cost_analysis()
        assert 'overall_efficiency' in analysis
        assert 'optimization_suggestions' in analysis
        assert 'model_usage' in analysis
        assert 'task_usage' in analysis


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self):
        """测试完整分析工作流"""
        # 创建模拟服务
        llm_manager = LLMServiceManager()
        
        # 模拟字幕内容
        subtitle_content = json.dumps({
            "body": [
                {"content": "Python是一种高级编程语言"},
                {"content": "它具有简洁的语法和强大的功能"},
                {"content": "被广泛应用于Web开发、数据科学等领域"}
            ]
        })
        
        # 模拟LLM响应
        mock_response = Mock()
        mock_response.content = json.dumps({
            "summary": "Python是一种高级编程语言，具有简洁语法和强大功能，广泛应用于Web开发和数据科学。",
            "key_points": [
                "Python是高级编程语言",
                "语法简洁",
                "功能强大",
                "应用广泛"
            ],
            "categories": ["编程", "教育", "技术"],
            "tags": ["Python", "编程语言", "Web开发", "数据科学"],
            "knowledge_entries": [
                {
                    "title": "Python编程语言",
                    "content": "Python是一种高级编程语言",
                    "type": "concept",
                    "importance": 5
                }
            ]
        })
        mock_response.tokens_used = 150
        mock_response.cost = 0.02
        mock_response.latency = 1.5
        
        with patch.object(llm_manager, 'chat', new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_response
            
            # 创建分析器
            analyzer = ContentAnalyzer(llm_manager)
            
            # 执行分析
            result = await analyzer.analyze_subtitle(subtitle_content)
            
            # 验证结果
            assert isinstance(result, AnalysisResult)
            assert "Python" in result.summary
            assert len(result.key_points) == 4
            assert "编程" in result.categories
            assert "Python" in result.tags
            assert len(result.knowledge_entries) == 1
            assert result.total_tokens == 150
            assert result.total_cost == 0.02
            assert result.analysis_time > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])