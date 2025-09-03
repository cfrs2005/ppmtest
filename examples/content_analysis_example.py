"""
大模型内容分析模块使用示例
"""

import asyncio
import json
import logging
from datetime import datetime

from bilibili_analyzer.services import (
    LLMServiceManager, 
    ModelConfig, 
    LLMProvider, 
    ModelType,
    AnalysisService
)
from bilibili_analyzer.analyzers import ContentAnalyzer, AnalysisConfig
from bilibili_analyzer.cache import CacheManager, CacheConfig
from bilibili_analyzer.utils import TokenManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_analysis():
    """基础分析示例"""
    print("=== 基础分析示例 ===")
    
    # 1. 初始化LLM服务管理器
    llm_manager = LLMServiceManager()
    
    # 2. 添加OpenAI服务（需要API密钥）
    try:
        openai_config = ModelConfig(
            provider=LLMProvider.OPENAI,
            model=ModelType.GPT_3_5_TURBO,
            max_tokens=4000,
            temperature=0.7
        )
        
        # 注意：这里需要真实的API密钥
        # openai_service = LLMServiceFactory.create_service(
        #     LLMProvider.OPENAI,
        #     "your-openai-api-key",
        #     openai_config
        # )
        # llm_manager.add_service("openai-gpt35", openai_service, is_default=True)
        
        print("OpenAI服务配置完成")
        
    except Exception as e:
        print(f"OpenAI服务配置失败: {e}")
    
    # 3. 创建分析服务
    analysis_service = AnalysisService(llm_manager)
    
    # 4. 示例字幕内容
    sample_subtitle = json.dumps({
        "body": [
            {"content": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。"},
            {"content": "它具有简洁的语法和强大的功能，被广泛应用于Web开发、数据科学、人工智能等领域。"},
            {"content": "Python的特点包括：易读易写、丰富的库支持、跨平台兼容性。"},
            {"content": "学习Python相对简单，是初学者的理想选择。"},
            {"content": "Python社区活跃，有大量的学习资源和支持。"}
        ]
    })
    
    # 5. 执行分析（使用模拟响应）
    try:
        result = await analysis_service.analyze_subtitle_content(sample_subtitle)
        print(f"分析完成！")
        print(f"总结: {result.summary}")
        print(f"关键点: {result.key_points}")
        print(f"分类: {result.categories}")
        print(f"标签: {result.tags}")
        print(f"使用Token: {result.total_tokens}")
        print(f"成本: ${result.total_cost:.4f}")
        
    except Exception as e:
        print(f"分析失败: {e}")


async def example_chunked_analysis():
    """分块分析示例"""
    print("\n=== 分块分析示例 ===")
    
    # 创建长文本内容
    long_content = """
    人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。
    
    机器学习是人工智能的一个子领域，它使计算机能够从数据中学习和改进，而无需明确编程。
    深度学习是机器学习的一个子集，使用神经网络来模拟人脑的工作方式。
    
    自然语言处理（NLP）是人工智能的一个重要应用领域，专注于计算机与人类语言之间的交互。
    计算机视觉是另一个重要领域，使计算机能够理解和解释视觉信息。
    
    人工智能的应用包括：语音识别、图像识别、推荐系统、自动驾驶、医疗诊断等。
    随着技术的发展，AI正在改变我们的生活和工作方式。
    
    然而，AI也带来了一些挑战，包括隐私问题、就业影响、伦理考量等。
    负责任的AI开发需要考虑这些因素，确保技术的发展造福人类社会。
    
    未来，人工智能将继续发展，可能带来更多的创新和变革。
    我们需要平衡技术进步与社会责任，共同塑造AI的未来。
    """ * 3  # 重复内容以创建更长的文本
    
    # 创建分析器
    llm_manager = LLMServiceManager()
    analyzer = ContentAnalyzer(
        llm_manager,
        AnalysisConfig(
            enable_chunking=True,
            max_tokens_per_chunk=500,  # 设置较小的chunk大小用于演示
            enable_caching=True,
            cache_ttl=3600
        )
    )
    
    # 模拟分析
    print(f"文本长度: {len(long_content)} 字符")
    print("开始分块分析...")
    
    # 这里应该有真实的LLM API调用
    # 为了演示，我们直接显示分块信息
    from bilibili_analyzer.analyzers.chunk_processor import ChunkProcessor
    chunk_processor = analyzer.chunk_processor
    
    chunks = chunk_processor.chunk_text(long_content)
    print(f"分块数量: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        tokens = chunk_processor.count_tokens(chunk.content)
        print(f"Chunk {i+1}: {tokens} tokens, {len(chunk.content)} 字符")


async def example_cache_usage():
    """缓存使用示例"""
    print("\n=== 缓存使用示例 ===")
    
    # 创建缓存管理器
    cache_config = CacheConfig(
        max_size=100,
        default_ttl=3600,
        enable_stats=True
    )
    
    cache_manager = CacheManager(cache_config)
    cache = cache_manager.get_memory_cache()
    
    # 测试缓存操作
    test_content = "这是一个测试内容"
    
    # 第一次获取（未缓存）
    result1 = cache.get("test_key")
    print(f"第一次获取结果: {result1}")
    
    # 设置缓存
    cache.set("test_key", test_content)
    print("已设置缓存")
    
    # 第二次获取（已缓存）
    result2 = cache.get("test_key")
    print(f"第二次获取结果: {result2}")
    
    # 查看统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")


async def example_token_management():
    """Token管理示例"""
    print("\n=== Token管理示例 ===")
    
    # 创建Token管理器
    token_manager = TokenManager(
        daily_token_limit=10000,
        daily_cost_limit=1.0
    )
    
    # 记录一些使用情况
    token_manager.record_usage(
        tokens=100,
        cost=0.01,
        model="gpt-3.5-turbo",
        task_type="analysis",
        content="示例内容"
    )
    
    token_manager.record_usage(
        tokens=200,
        cost=0.02,
        model="gpt-4",
        task_type="summary",
        content="示例内容2"
    )
    
    # 查看使用统计
    stats = token_manager.get_usage_stats()
    print(f"总Token使用: {stats.total_tokens}")
    print(f"总成本: ${stats.total_cost:.4f}")
    
    # 查看限制状态
    limit_status = token_manager.get_limit_status()
    print(f"剩余Token: {limit_status['remaining_tokens']}")
    print(f"剩余预算: ${limit_status['remaining_cost']:.4f}")
    
    # 测试限制检查
    can_use = token_manager.check_limit(5000, 0.5)
    print(f"是否可以使用5000 tokens: {can_use}")


async def example_analysis_service():
    """分析服务完整示例"""
    print("\n=== 分析服务完整示例 ===")
    
    # 创建分析服务
    analysis_service = AnalysisService()
    
    # 获取服务统计
    stats = analysis_service.get_analysis_stats()
    print("服务统计:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}: {len(value) if hasattr(value, '__len__') else 'N/A'}")
        else:
            print(f"  {key}: {value}")
    
    # 获取成本分析
    cost_analysis = analysis_service.get_cost_analysis()
    print(f"\n成本分析:")
    print(f"  优化建议数量: {len(cost_analysis['optimization_suggestions'])}")
    
    # 清理缓存
    analysis_service.cleanup_cache()
    print("缓存已清理")


async def example_error_handling():
    """错误处理示例"""
    print("\n=== 错误处理示例 ===")
    
    analysis_service = AnalysisService()
    
    # 测试空内容
    try:
        await analysis_service.analyze_subtitle_content("")
    except Exception as e:
        print(f"空内容错误: {e}")
    
    # 测试无效JSON
    try:
        await analysis_service.analyze_subtitle_content("invalid json", "json")
    except Exception as e:
        print(f"无效JSON错误: {e}")
    
    # 测试Token限制
    token_manager = analysis_service.token_manager
    try:
        # 设置很小的限制
        token_manager.limits[token_manager.limits.__class__.DAILY].max_tokens = 10
        
        # 尝试分析大量内容
        large_content = "x" * 1000
        await analysis_service.analyze_subtitle_content(large_content)
    except Exception as e:
        print(f"Token限制错误: {e}")


async def main():
    """主函数"""
    print("大模型内容分析模块示例")
    print("=" * 50)
    
    try:
        # 运行各种示例
        await example_basic_analysis()
        await example_chunked_analysis()
        await example_cache_usage()
        await example_token_management()
        await example_analysis_service()
        await example_error_handling()
        
        print("\n所有示例运行完成！")
        
    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())