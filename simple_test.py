#!/usr/bin/env python3
"""
简单验证脚本 - 测试大模型内容分析模块的基本功能
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """测试导入"""
    print("=== 测试模块导入 ===")
    
    try:
        # 测试LLM服务
        from bilibili_analyzer.services import (
            LLMServiceManager, ModelConfig, LLMProvider, ModelType,
            LLMMessage, LLMResponse
        )
        print("✅ LLM服务模块导入成功")
        
        # 测试分析器
        from bilibili_analyzer.analyzers import (
            ContentAnalyzer, AnalysisResult, ChunkProcessor, TextPreprocessor
        )
        print("✅ 分析器模块导入成功")
        
        # 测试缓存
        from bilibili_analyzer.cache import CacheManager, CacheConfig
        print("✅ 缓存模块导入成功")
        
        # 测试配置
        from bilibili_analyzer.config.analysis_config import (
            LLM_CONFIG, ANALYSIS_CONFIG, TOKEN_LIMITS
        )
        print("✅ 配置模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    try:
        from bilibili_analyzer.services import LLMServiceManager, ModelConfig, LLMProvider, ModelType
        from bilibili_analyzer.analyzers import ContentAnalyzer, AnalysisConfig
        from bilibili_analyzer.cache import CacheManager
        
        # 创建LLM管理器
        llm_manager = LLMServiceManager()
        print("✅ LLM管理器创建成功")
        
        # 创建缓存管理器
        cache_manager = CacheManager()
        print("✅ 缓存管理器创建成功")
        
        # 创建分析器
        analyzer = ContentAnalyzer(llm_manager, AnalysisConfig())
        print("✅ 内容分析器创建成功")
        
        # 测试缓存操作
        cache = cache_manager.get_memory_cache()
        cache.set("test", "value")
        assert cache.get("test") == "value"
        print("✅ 缓存读写正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def test_configuration():
    """测试配置"""
    print("\n=== 测试配置 ===")
    
    try:
        from bilibili_analyzer.config.analysis_config import (
            LLM_CONFIG, ANALYSIS_CONFIG, TOKEN_LIMITS
        )
        
        # 检查配置结构
        assert 'openai' in LLM_CONFIG
        assert 'anthropic' in LLM_CONFIG
        assert 'enable_chunking' in ANALYSIS_CONFIG
        assert 'daily_token_limit' in TOKEN_LIMITS
        
        print("✅ 配置结构正确")
        
        # 检查具体配置值
        assert ANALYSIS_CONFIG['enable_chunking'] == True
        assert ANALYSIS_CONFIG['max_tokens_per_chunk'] == 2000
        assert TOKEN_LIMITS['daily_token_limit'] == 100000
        
        print("✅ 配置值正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def main():
    """主函数"""
    print("大模型内容分析模块验证")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_configuration
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