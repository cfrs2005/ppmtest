"""
大模型内容分析模块示例配置
"""

import os
from typing import Dict, Any

# LLM API配置
LLM_CONFIG = {
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "default_model": "gpt-3.5-turbo",
        "models": {
            "gpt-3.5-turbo": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 30
            },
            "gpt-4": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 60
            },
            "gpt-4-turbo": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 45
            },
            "gpt-4o": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 30
            }
        }
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
        "default_model": "claude-3-haiku-20240307",
        "models": {
            "claude-3-haiku-20240307": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 30
            },
            "claude-3-sonnet-20240229": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 45
            },
            "claude-3-opus-20240229": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 60
            }
        }
    },
    "glm": {
        "api_key": os.getenv("GLM_API_KEY", ""),
        "base_url": os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4"),
        "default_model": "glm-4-flash",
        "models": {
            "glm-4-flash": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 30
            },
            "glm-4-air": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 45
            },
            "glm-4-vision": {
                "max_tokens": 4000,
                "temperature": 0.7,
                "timeout": 60
            }
        }
    }
}

# 分析配置
ANALYSIS_CONFIG = {
    "enable_chunking": True,
    "max_tokens_per_chunk": 2000,
    "min_tokens_per_chunk": 100,
    "overlap_tokens": 200,
    "enable_caching": True,
    "cache_ttl": 3600,  # 1小时
    "enable_knowledge_extraction": True,
    "max_knowledge_entries": 20,
    "semantic_chunking": True,
    "respect_sentence_boundaries": True
}

# 缓存配置
CACHE_CONFIG = {
    "max_size": 1000,
    "default_ttl": 3600,
    "cleanup_interval": 300,
    "enable_compression": True,
    "enable_stats": True
}

# Token限制配置
TOKEN_LIMITS = {
    "daily_token_limit": 100000,
    "daily_cost_limit": 10.0,
    "weekly_token_limit": 500000,
    "weekly_cost_limit": 50.0,
    "monthly_token_limit": 2000000,
    "monthly_cost_limit": 200.0
}

# 成本控制配置
COST_CONTROL = {
    "enable_cost_monitoring": True,
    "cost_alert_threshold": 0.8,  # 达到限制的80%时发出警告
    "auto_model_switch": True,    # 自动切换到更便宜的模型
    "budget_tracking": True       # 预算跟踪
}

# 分析模板
ANALYSIS_TEMPLATES = {
    "summary": {
        "system_prompt": """你是一个专业的内容总结助手。请为给定的文本生成一个简洁明了的总结（100-200字）。

要求：
1. 抓住核心内容和主要观点
2. 逻辑清晰，层次分明
3. 语言简洁，避免冗余
4. 保持客观性和准确性""",
        "user_prompt": "请总结以下内容：\n\n{content}"
    },
    "key_points": {
        "system_prompt": """你是一个专业的内容分析助手。请从给定的文本中提取5-10个关键点。

要求：
1. 每个关键点应该简洁明了
2. 包含重要信息和核心观点
3. 逻辑顺序合理
4. 避免重复和冗余""",
        "user_prompt": "请提取以下内容的关键点：\n\n{content}"
    },
    "categories": {
        "system_prompt": """你是一个专业的内容分类助手。请为给定的文本内容进行分类。

要求：
1. 提供3-5个最相关的分类标签
2. 分类应该准确反映内容主题
3. 使用标准的分类体系
4. 避免过于宽泛或过于具体的分类""",
        "user_prompt": "请分类以下内容：\n\n{content}"
    },
    "tags": {
        "system_prompt": """你是一个专业的标签生成助手。请为给定的文本内容生成标签。

要求：
1. 提供10-15个相关标签
2. 标签应该简洁、准确、具有代表性
3. 覆盖内容的主要方面
4. 使用常见的标签格式""",
        "user_prompt": "请为以下内容生成标签：\n\n{content}"
    },
    "knowledge_extraction": {
        "system_prompt": """你是一个专业的知识提取助手。请从给定的文本中提取结构化的知识条目。

返回格式必须为JSON，包含以下字段：
- title: 知识条目标题
- content: 详细内容
- type: 知识类型（concept/fact/method/tip）
- importance: 重要性等级（1-5）
- tags: 相关标签列表

要求：
1. 提取真正有价值的知识点
2. 结构化呈现，便于后续使用
3. 评估重要性等级
4. 提供相关的标签""",
        "user_prompt": "请从以下内容中提取知识条目：\n\n{content}"
    }
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_concurrent_requests": 5,
    "request_timeout": 30,
    "retry_attempts": 3,
    "retry_delay": 1,
    "batch_processing": True,
    "batch_size": 10,
    "enable_progress_tracking": True
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "analysis.log",
            "level": "DEBUG"
        }
    }
}

# 数据库配置
DATABASE_CONFIG = {
    "analysis_table_name": "analyses",
    "knowledge_table_name": "knowledge_entries",
    "batch_insert_size": 100,
    "enable_connection_pool": True,
    "connection_timeout": 30
}

def get_llm_config(provider: str) -> Dict[str, Any]:
    """获取指定提供商的配置"""
    return LLM_CONFIG.get(provider, {})

def get_model_config(provider: str, model: str) -> Dict[str, Any]:
    """获取指定模型的配置"""
    provider_config = get_llm_config(provider)
    return provider_config.get("models", {}).get(model, {})

def get_analysis_template(template_name: str) -> Dict[str, str]:
    """获取分析模板"""
    return ANALYSIS_TEMPLATES.get(template_name, {})

def validate_config() -> bool:
    """验证配置是否有效"""
    required_keys = [
        "openai.api_key",
        "anthropic.api_key",
        "glm.api_key"
    ]
    
    for key in required_keys:
        provider, config_key = key.split(".")
        if not LLM_CONFIG[provider].get(config_key):
            print(f"警告: 缺少配置 {key}")
            return False
    
    return True

def print_config_summary():
    """打印配置摘要"""
    print("=== 大模型内容分析模块配置摘要 ===")
    print(f"OpenAI API配置: {'已配置' if LLM_CONFIG['openai']['api_key'] else '未配置'}")
    print(f"Anthropic API配置: {'已配置' if LLM_CONFIG['anthropic']['api_key'] else '未配置'}")
    print(f"GLM API配置: {'已配置' if LLM_CONFIG['glm']['api_key'] else '未配置'}")
    print(f"分块处理: {'启用' if ANALYSIS_CONFIG['enable_chunking'] else '禁用'}")
    print(f"缓存机制: {'启用' if ANALYSIS_CONFIG['enable_caching'] else '禁用'}")
    print(f"知识提取: {'启用' if ANALYSIS_CONFIG['enable_knowledge_extraction'] else '禁用'}")
    print(f"每日Token限制: {TOKEN_LIMITS['daily_token_limit']:,}")
    print(f"每日成本限制: ${TOKEN_LIMITS['daily_cost_limit']:.2f}")
    print("=" * 50)

if __name__ == "__main__":
    print_config_summary()
    validate_config()