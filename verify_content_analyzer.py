#!/usr/bin/env python3
"""
大模型内容分析模块功能验证脚本
"""

import sys
import os
sys.path.append('.')
import asyncio
import json
import time

def test_core_modules():
    """测试核心模块"""
    print("=== 测试核心模块 ===")
    
    try:
        # 测试LLM服务
        from bilibili_analyzer.services.llm import (
            LLMServiceManager, ModelConfig, LLMProvider, ModelType,
            LLMMessage, LLMResponse
        )
        
        # 创建服务管理器
        manager = LLMServiceManager()
        print("✅ LLM服务管理器创建成功")
        
        # 测试模型配置
        config = ModelConfig(
            provider=LLMProvider.OPENAI,
            model=ModelType.GPT_3_5_TURBO,
            max_tokens=1000
        )
        print("✅ 模型配置创建成功")
        
        # 测试消息
        message = LLMMessage(role="user", content="Hello")
        print("✅ LLM消息创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 核心模块测试失败: {e}")
        return False

def test_cache_system():
    """测试缓存系统"""
    print("\n=== 测试缓存系统 ===")
    
    try:
        from bilibili_analyzer.cache import CacheManager, CacheConfig
        
        # 创建缓存管理器
        config = CacheConfig(max_size=100, default_ttl=3600)
        cache_manager = CacheManager(config)
        print("✅ 缓存管理器创建成功")
        
        # 测试基本操作
        cache = cache_manager.get_memory_cache()
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        
        assert value == "test_value"
        print("✅ 缓存基本操作正常")
        
        # 测试统计
        stats = cache.get_stats()
        assert 'hits' in stats
        assert 'misses' in stats
        print("✅ 缓存统计功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存系统测试失败: {e}")
        return False

def test_token_management():
    """测试Token管理"""
    print("\n=== 测试Token管理 ===")
    
    try:
        from bilibili_analyzer.utils.token_manager import TokenManager
        
        # 创建Token管理器
        token_manager = TokenManager(
            daily_token_limit=10000,
            daily_cost_limit=1.0
        )
        print("✅ Token管理器创建成功")
        
        # 测试使用记录
        token_manager.record_usage(
            tokens=100,
            cost=0.01,
            model="gpt-3.5-turbo",
            task_type="test",
            content="test content"
        )
        print("✅ Token使用记录成功")
        
        # 测试限制检查
        can_use = token_manager.check_limit(1000, 0.1)
        assert can_use == True
        print("✅ Token限制检查正常")
        
        # 测试统计
        stats = token_manager.get_usage_stats()
        assert stats.total_tokens == 100
        assert stats.total_cost == 0.01
        print("✅ Token统计功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ Token管理测试失败: {e}")
        return False

def test_text_processing():
    """测试文本处理"""
    print("\n=== 测试文本处理 ===")
    
    try:
        from bilibili_analyzer.analyzers.text_preprocessor import TextPreprocessor
        
        # 创建预处理器
        preprocessor = TextPreprocessor()
        print("✅ 文本预处理器创建成功")
        
        # 测试文本清理
        text = """
        这是一个测试
        
        666
        哈哈哈哈
        ！！！
        
        正常内容
        """
        
        cleaned = preprocessor.clean_text(text)
        assert "666" not in cleaned
        assert "哈哈哈" not in cleaned
        assert "正常内容" in cleaned
        print("✅ 文本清理功能正常")
        
        # 测试句子提取
        sentences = preprocessor.extract_sentences("这是第一句。这是第二句！")
        assert len(sentences) == 2
        print("✅ 句子提取功能正常")
        
        # 测试统计
        stats = preprocessor.get_text_stats("测试文本")
        assert 'total_chars' in stats
        assert 'chinese_chars' in stats
        print("✅ 文本统计功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 文本处理测试失败: {e}")
        return False

def test_chunking():
    """测试分块处理"""
    print("\n=== 测试分块处理 ===")
    
    try:
        from bilibili_analyzer.analyzers.chunk_processor import ChunkProcessor, ChunkConfig
        
        # 创建分块处理器
        config = ChunkConfig(max_tokens=100)
        processor = ChunkProcessor(config)
        print("✅ 分块处理器创建成功")
        
        # 测试分块
        text = "这是一个测试句子。" * 20
        chunks = processor.chunk_text(text)
        assert len(chunks) > 1
        print("✅ 文本分块功能正常")
        
        # 测试Token计数
        tokens = processor.count_tokens(text)
        assert tokens > 0
        print("✅ Token计数功能正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 分块处理测试失败: {e}")
        return False

def test_configuration():
    """测试配置系统"""
    print("\n=== 测试配置系统 ===")
    
    try:
        from bilibili_analyzer.config.analysis_config import (
            LLM_CONFIG, ANALYSIS_CONFIG, TOKEN_LIMITS
        )
        
        # 测试LLM配置
        assert 'openai' in LLM_CONFIG
        assert 'anthropic' in LLM_CONFIG
        print("✅ LLM配置加载成功")
        
        # 测试分析配置
        assert 'enable_chunking' in ANALYSIS_CONFIG
        assert 'max_tokens_per_chunk' in ANALYSIS_CONFIG
        print("✅ 分析配置加载成功")
        
        # 测试Token限制
        assert 'daily_token_limit' in TOKEN_LIMITS
        assert 'daily_cost_limit' in TOKEN_LIMITS
        print("✅ Token限制配置加载成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False

def run_performance_test():
    """运行性能测试"""
    print("\n=== 运行性能测试 ===")
    
    try:
        from bilibili_analyzer.cache import CacheManager, CacheConfig
        
        # 测试缓存性能
        config = CacheConfig(max_size=1000, default_ttl=3600)
        cache_manager = CacheManager(config)
        cache = cache_manager.get_memory_cache()
        
        # 测试写入性能
        start_time = time.time()
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")
        write_time = time.time() - start_time
        
        # 测试读取性能
        start_time = time.time()
        for i in range(100):
            value = cache.get(f"key_{i}")
        read_time = time.time() - start_time
        
        print(f"✅ 缓存写入性能: {write_time*1000:.2f}ms (100次)")
        print(f"✅ 缓存读取性能: {read_time*1000:.2f}ms (100次)")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False

def main():
    """主函数"""
    print("大模型内容分析模块功能验证")
    print("=" * 50)
    
    tests = [
        test_core_modules,
        test_cache_system,
        test_token_management,
        test_text_processing,
        test_chunking,
        test_configuration,
        run_performance_test
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！大模型内容分析模块实现成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)