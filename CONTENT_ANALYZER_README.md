# 大模型内容分析模块

## 概述

大模型内容分析模块是B站视频分析系统的核心组件，负责对字幕内容进行智能分析，提取关键信息，生成结构化知识库。该模块集成了OpenAI和Anthropic的API服务，提供了完整的文本分析、缓存管理、成本控制和性能优化功能。

## 核心功能

### 1. LLM服务抽象层
- **多厂商支持**：统一接口支持OpenAI GPT系列和Anthropic Claude系列
- **模型管理**：支持多种模型配置和动态切换
- **错误处理**：自动重试和降级处理
- **成本统计**：实时计算API调用成本

### 2. 内容分析器
- **智能分块**：基于语义的智能分块处理
- **多维分析**：总结、关键点、分类、标签、知识提取
- **结果整合**：多分块结果的智能合并
- **质量控制**：分析结果的质量评估和过滤

### 3. 缓存管理
- **多层缓存**：内存缓存和Redis缓存支持
- **智能失效**：基于TTL和LRU的缓存策略
- **统计监控**：缓存命中率和性能统计
- **数据压缩**：可选的缓存数据压缩

### 4. Token管理
- **使用限制**：支持日/周/月Token使用限制
- **成本控制**：实时成本监控和预警
- **效率分析**：成本效率评估和优化建议
- **模型推荐**：基于预算的模型推荐

### 5. 性能优化
- **并发处理**：支持并发API调用
- **批处理**：批量处理提高效率
- **连接池**：数据库和HTTP连接池
- **资源管理**：内存和CPU资源优化

## 架构设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Services  │    │  Content Analyzer│    │  Cache Manager  │
│                 │    │                 │    │                 │
│ • OpenAI API    │◄──►│ • Text Preprocessing│◄──►│ • Memory Cache  │
│ • Anthropic API │    │ • Chunk Processor │    │ • Redis Cache   │
│ • Model Config  │    │ • Analysis Logic │    │ • Cache Stats   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Token Manager   │    │ Database Layer  │    │ Performance     │
│                 │    │                 │    │                 │
│ • Usage Tracking│    │ • Analysis Model │    │ • Metrics       │
│ • Cost Control  │    │ • Knowledge Base│    │ • Optimization  │
│ • Limits        │    │ • Query Engine  │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 安装配置

### 1. 依赖安装

```bash
pip install -r requirements.txt
```

### 2. 环境配置

创建`.env`文件：

```env
# OpenAI配置
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic配置
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# 数据库配置
DATABASE_URL=sqlite:///instance/app.db
```

### 3. 模块配置

编辑`bilibili_analyzer/config/analysis_config.py`：

```python
# LLM配置
LLM_CONFIG = {
    "openai": {
        "api_key": "your-openai-api-key",
        "default_model": "gpt-3.5-turbo",
        "models": {
            "gpt-3.5-turbo": {
                "max_tokens": 4000,
                "temperature": 0.7
            }
        }
    }
}

# 分析配置
ANALYSIS_CONFIG = {
    "enable_chunking": True,
    "max_tokens_per_chunk": 2000,
    "enable_caching": True,
    "cache_ttl": 3600
}

# Token限制
TOKEN_LIMITS = {
    "daily_token_limit": 100000,
    "daily_cost_limit": 10.0
}
```

## 使用示例

### 1. 基础分析

```python
import asyncio
from bilibili_analyzer.services import AnalysisService

async def basic_analysis():
    # 创建分析服务
    service = AnalysisService()
    
    # 字幕内容
    subtitle_content = '''
    {
        "body": [
            {"content": "Python是一种高级编程语言"},
            {"content": "它具有简洁的语法和强大的功能"}
        ]
    }
    '''
    
    # 执行分析
    result = await service.analyze_subtitle_content(subtitle_content)
    
    print(f"总结: {result.summary}")
    print(f"关键点: {result.key_points}")
    print(f"分类: {result.categories}")
    print(f"标签: {result.tags}")

asyncio.run(basic_analysis())
```

### 2. 视频分析

```python
async def video_analysis():
    service = AnalysisService()
    
    # 分析视频（需要数据库中的视频ID）
    result = await service.analyze_video(video_id=1)
    
    print(f"分析完成，使用了 {result.total_tokens} tokens")
    print(f"成本: ${result.total_cost:.4f}")

asyncio.run(video_analysis())
```

### 3. 缓存使用

```python
from bilibili_analyzer.cache import CacheManager, CacheConfig

# 创建缓存管理器
cache_config = CacheConfig(max_size=1000, default_ttl=3600)
cache_manager = CacheManager(cache_config)

# 使用缓存
cache = cache_manager.get_memory_cache()
cache.set("key", "value")
value = cache.get("key")
```

### 4. Token管理

```python
from bilibili_analyzer.utils import TokenManager

# 创建Token管理器
token_manager = TokenManager(
    daily_token_limit=100000,
    daily_cost_limit=10.0
)

# 检查限制
if token_manager.check_limit(1000, 0.01):
    # 执行分析
    token_manager.record_usage(1000, 0.01, "gpt-3.5-turbo", "analysis")

# 获取统计
stats = token_manager.get_usage_stats()
print(f"今日使用: {stats.total_tokens} tokens")
```

## 性能测试

运行性能测试：

```bash
python tests/test_performance.py
```

测试内容包括：
- 分析性能测试
- 缓存性能测试
- 分块性能测试
- 并发处理测试
- 内存使用测试
- 成本效率测试

## API文档

### ContentAnalyzer

#### analyze_subtitle(content, format, service_name)
分析字幕内容

**参数:**
- `content`: 字幕内容
- `format`: 字幕格式 (json/srt)
- `service_name`: LLM服务名称

**返回:** AnalysisResult

#### generate_summary(content, service_name)
生成内容总结

**参数:**
- `content`: 文本内容
- `service_name`: LLM服务名称

**返回:** str

### AnalysisService

#### analyze_video(video_id, force_reanalysis)
分析视频

**参数:**
- `video_id`: 视频ID
- `force_reanalysis`: 是否强制重新分析

**返回:** AnalysisResult

#### get_analysis_stats()
获取分析统计

**返回:** Dict[str, Any]

### TokenManager

#### record_usage(tokens, cost, model, task_type, content)
记录Token使用

**参数:**
- `tokens`: Token数量
- `cost`: 成本
- `model`: 模型名称
- `task_type`: 任务类型
- `content`: 内容标识

#### check_limit(tokens, cost, limit_type)
检查使用限制

**参数:**
- `tokens`: Token数量
- `cost`: 成本
- `limit_type`: 限制类型

**返回:** bool

## 配置选项

### LLM配置
- `provider`: 服务提供商 (openai/anthropic)
- `model`: 模型名称
- `max_tokens`: 最大Token数
- `temperature`: 温度参数
- `timeout`: 超时时间

### 分析配置
- `enable_chunking`: 启用分块处理
- `max_tokens_per_chunk`: 每块最大Token数
- `enable_caching`: 启用缓存
- `cache_ttl`: 缓存过期时间
- `enable_knowledge_extraction`: 启用知识提取

### 缓存配置
- `max_size`: 最大缓存数量
- `default_ttl`: 默认过期时间
- `enable_compression`: 启用压缩
- `cleanup_interval`: 清理间隔

### Token限制
- `daily_token_limit`: 日Token限制
- `daily_cost_limit`: 日成本限制
- `weekly_token_limit`: 周Token限制
- `weekly_cost_limit`: 周成本限制

## 错误处理

### 常见错误
1. **API密钥错误**: 检查环境变量配置
2. **Token超限**: 检查使用统计和限制配置
3. **网络错误**: 检查网络连接和代理设置
4. **数据库错误**: 检查数据库连接和权限

### 错误处理示例

```python
try:
    result = await service.analyze_subtitle_content(content)
except ValueError as e:
    print(f"参数错误: {e}")
except ConnectionError as e:
    print(f"网络错误: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

## 优化建议

### 1. 性能优化
- 使用缓存减少API调用
- 合理设置分块大小
- 启用并发处理
- 优化数据库查询

### 2. 成本优化
- 选择合适的模型
- 启用智能缓存
- 监控使用情况
- 设置合理的限制

### 3. 质量优化
- 调整提示词模板
- 优化分块策略
- 结果后处理
- 质量评估和过滤

## 监控和日志

### 性能监控
- API调用时间
- 缓存命中率
- Token使用量
- 成本统计

### 日志配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 扩展开发

### 添加新的LLM提供商
1. 继承`BaseLLMService`类
2. 实现`chat`、`count_tokens`、`estimate_cost`方法
3. 在`LLMServiceFactory`中注册

### 自定义分析逻辑
1. 继承`ContentAnalyzer`类
2. 重写分析方法
3. 添加自定义提示词模板

### 扩展缓存后端
1. 实现缓存接口
2. 支持Redis、Memcached等
3. 添加分布式缓存支持

## 许可证

本项目采用MIT许可证。

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 支持和反馈

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 参与讨论

---

**注意**: 使用本模块需要有效的OpenAI或Anthropic API密钥，相关费用由用户承担。