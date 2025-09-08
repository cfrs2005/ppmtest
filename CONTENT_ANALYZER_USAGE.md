# 大模型内容分析模块使用指南

## 概述

本模块提供了完整的字幕内容智能分析功能，支持多种大模型API，具备智能分块、缓存管理、成本控制等特性。

## 功能特性

### ✅ 已实现功能

1. **多模型支持**
   - OpenAI GPT系列 (GPT-3.5-turbo, GPT-4, GPT-4-turbo, GPT-4o)
   - Anthropic Claude系列 (Claude-3-haiku, Claude-3-sonnet, Claude-3-opus)

2. **智能内容分析**
   - 内容总结生成 (100-200字)
   - 关键点提取 (5-10个要点)
   - 智能分类 (3-5个分类标签)
   - 标签生成 (10-15个相关标签)
   - 知识条目构建 (结构化知识提取)

3. **智能分块处理**
   - 基于Token限制的语义分块
   - 句子边界保持
   - 重叠区域处理
   - 长文本优化

4. **缓存管理**
   - 内存缓存支持
   - TTL过期管理
   - LRU淘汰策略
   - 统计信息跟踪

5. **成本控制**
   - Token使用统计
   - 成本预算控制
   - 多层级限制 (日/周/月)
   - 自动模型推荐

6. **错误处理**
   - 重试机制
   - 降级处理
   - 异常恢复

## 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.template .env

# 编辑 .env 文件，填入你的API密钥
# OPENAI_API_KEY=your-openai-api-key-here
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### 2. 基本使用

```python
import asyncio
import json
from bilibili_analyzer.services import LLMServiceManager, ModelConfig, LLMProvider, ModelType
from bilibili_analyzer.analyzers import ContentAnalyzer, AnalysisConfig

async def main():
    # 1. 创建LLM服务管理器
    llm_manager = LLMServiceManager()
    
    # 2. 添加OpenAI服务
    config = ModelConfig(
        provider=LLMProvider.OPENAI,
        model=ModelType.GPT_3_5_TURBO,
        max_tokens=4000,
        temperature=0.7
    )
    
    # 注意：需要真实的API密钥
    # openai_service = LLMServiceFactory.create_service(
    #     LLMProvider.OPENAI,
    #     "your-api-key",
    #     config
    # )
    # llm_manager.add_service("openai", openai_service, is_default=True)
    
    # 3. 创建分析器
    analyzer = ContentAnalyzer(llm_manager)
    
    # 4. 准备字幕内容
    subtitle_content = json.dumps({
        "body": [
            {"content": "Python是一种高级编程语言"},
            {"content": "它具有简洁的语法和强大的功能"},
            {"content": "被广泛应用于Web开发、数据科学等领域"}
        ]
    })
    
    # 5. 执行分析
    result = await analyzer.analyze_subtitle(subtitle_content)
    
    # 6. 查看结果
    print(f"总结: {result.summary}")
    print(f"关键点: {result.key_points}")
    print(f"分类: {result.categories}")
    print(f"标签: {result.tags}")
    print(f"使用Token: {result.total_tokens}")
    print(f"成本: ${result.total_cost:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. 高级配置

```python
from bilibili_analyzer.analyzers import AnalysisConfig
from bilibili_analyzer.cache import CacheConfig
from bilibili_analyzer.utils import TokenManager

# 自定义分析配置
analysis_config = AnalysisConfig(
    enable_chunking=True,
    max_tokens_per_chunk=2000,
    enable_caching=True,
    cache_ttl=3600,
    enable_knowledge_extraction=True,
    max_knowledge_entries=20
)

# 自定义缓存配置
cache_config = CacheConfig(
    max_size=1000,
    default_ttl=3600,
    cleanup_interval=300,
    enable_compression=True
)

# Token管理器
token_manager = TokenManager(
    daily_token_limit=100000,
    daily_cost_limit=10.0
)
```

## 配置说明

### 模型配置

```python
# OpenAI 模型配置
LLM_CONFIG = {
    "openai": {
        "api_key": "your-api-key",
        "default_model": "gpt-3.5-turbo",
        "models": {
            "gpt-3.5-turbo": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 30
            }
        }
    }
}
```

### 分析配置

```python
ANALYSIS_CONFIG = {
    "enable_chunking": True,              # 启用分块处理
    "max_tokens_per_chunk": 2000,       # 每块最大Token数
    "enable_caching": True,              # 启用缓存
    "cache_ttl": 3600,                  # 缓存时间(秒)
    "enable_knowledge_extraction": True, # 启用知识提取
    "max_knowledge_entries": 20          # 最大知识条目数
}
```

### 成本控制

```python
TOKEN_LIMITS = {
    "daily_token_limit": 100000,     # 每日Token限制
    "daily_cost_limit": 10.0,        # 每日成本限制($)
    "weekly_token_limit": 500000,    # 每周Token限制
    "weekly_cost_limit": 50.0,       # 每周成本限制($)
    "monthly_token_limit": 2000000,  # 每月Token限制
    "monthly_cost_limit": 200.0      # 每月成本限制($)
}
```

## API 参考

### ContentAnalyzer

主要的内容分析类，提供以下方法：

- `analyze_subtitle(subtitle_content, subtitle_format, service_name)` - 分析字幕内容
- `generate_summary(content, service_name)` - 生成总结
- `extract_key_points(content, service_name)` - 提取关键点
- `categorize_content(content, service_name)` - 内容分类
- `generate_tags(content, service_name)` - 生成标签
- `build_knowledge_base(analysis_result)` - 构建知识库

### LLMServiceManager

LLM服务管理器，支持多个服务提供商：

- `add_service(name, service, is_default)` - 添加服务
- `get_service(name)` - 获取服务
- `chat(messages, service_name)` - 聊天接口
- `count_tokens(text, service_name)` - 计算Token数量

### CacheManager

缓存管理器：

- `get_memory_cache()` - 获取内存缓存
- `get_analysis_cache()` - 获取分析缓存
- `get_stats()` - 获取统计信息
- `cleanup()` - 清理缓存

### TokenManager

Token管理和成本控制：

- `record_usage(tokens, cost, model, task_type)` - 记录使用
- `check_limit(tokens, cost)` - 检查限制
- `get_usage_stats()` - 获取使用统计
- `get_limit_status()` - 获取限制状态

## 最佳实践

### 1. 成本优化

```python
# 选择合适的模型
def select_model(content_length, budget):
    if content_length < 1000:
        return "gpt-3.5-turbo"  # 短文本使用便宜模型
    elif budget > 5.0:
        return "gpt-4"          # 高预算使用高质量模型
    else:
        return "gpt-3.5-turbo"  # 默认选择
```

### 2. 缓存策略

```python
# 合理设置缓存时间
def get_cache_ttl(content_type):
    if content_type == "news":
        return 1800  # 新闻类内容缓存时间短
    elif content_type == "education":
        return 86400  # 教育类内容缓存时间长
    else:
        return 3600  # 默认1小时
```

### 3. 错误处理

```python
async def safe_analyze(analyzer, content):
    try:
        result = await analyzer.analyze_subtitle(content)
        return result
    except Exception as e:
        logger.error(f"分析失败: {e}")
        # 返回默认结果或重试
        return await fallback_analysis(content)
```

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的API密钥是否正确
   - 确认API密钥有足够的权限

2. **Token限制超出**
   - 检查Token使用统计
   - 调整限制或使用更便宜的模型

3. **缓存不工作**
   - 检查缓存配置
   - 确认缓存服务是否正常

4. **分析结果不准确**
   - 调整模型参数 (temperature, max_tokens)
   - 优化提示词

### 调试模式

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 查看详细统计
stats = token_manager.get_usage_stats()
print(f"Token使用统计: {stats}")

cache_stats = cache_manager.get_stats()
print(f"缓存统计: {cache_stats}")
```

## 性能优化

### 1. 批量处理

```python
async def batch_analyze(analyzer, contents):
    tasks = []
    for content in contents:
        task = asyncio.create_task(analyzer.analyze_subtitle(content))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 2. 并发控制

```python
import asyncio

async def analyze_with_semaphore(analyzer, content, semaphore):
    async with semaphore:
        return await analyzer.analyze_subtitle(content)

# 限制并发数
semaphore = asyncio.Semaphore(5)
tasks = [analyze_with_semaphore(analyzer, content, semaphore) 
         for content in contents]
```

## 示例项目

查看 `examples/content_analysis_example.py` 获取完整的使用示例。

## 许可证

本项目采用 MIT 许可证。