"""
大模型服务抽象层
支持OpenAI GPT系列和Claude系列
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

import openai
import anthropic
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GLM = "glm"


class ModelType(Enum):
    """模型类型枚举"""
    # OpenAI模型
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    
    # Anthropic模型
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    
    # GLM模型
    GLM_4_FLASH = "glm-4-flash"
    GLM_4_AIR = "glm-4-air"
    GLM_4_VISION = "glm-4-vision"


@dataclass
class LLMMessage:
    """LLM消息"""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model_used: str
    tokens_used: int
    cost: float
    latency: float


@dataclass
class ModelConfig:
    """模型配置"""
    provider: LLMProvider
    model: ModelType
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 1.0
    timeout: int = 30


class BaseLLMService(ABC):
    """LLM服务基类"""
    
    def __init__(self, api_key: str, config: ModelConfig):
        self.api_key = api_key
        self.config = config
        self.client = None
    
    @abstractmethod
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """聊天接口"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        """估算成本"""
        pass


class OpenAIService(BaseLLMService):
    """OpenAI服务实现"""
    
    # Token价格 (USD per 1K tokens)
    TOKEN_PRICES = {
        ModelType.GPT_3_5_TURBO: {"input": 0.0015, "output": 0.002},
        ModelType.GPT_4: {"input": 0.03, "output": 0.06},
        ModelType.GPT_4_TURBO: {"input": 0.01, "output": 0.03},
        ModelType.GPT_4O: {"input": 0.005, "output": 0.015},
    }
    
    def __init__(self, api_key: str, config: ModelConfig):
        super().__init__(api_key, config)
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """调用OpenAI API"""
        start_time = time.time()
        
        try:
            # 转换消息格式
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # 调用API
            response = await self.client.chat.completions.create(
                model=self.config.model.value,
                messages=openai_messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                timeout=self.config.timeout,
                **kwargs
            )
            
            # 计算统计信息
            latency = time.time() - start_time
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # 估算成本
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.config.model.value)
            return len(encoding.encode(text))
        except ImportError:
            # 简单估算：中文字符算2个token，英文单词算1.3个token
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_words = len(text.split()) - chinese_chars
            return int(chinese_chars * 2 + english_words * 1.3)
    
    def estimate_cost(self, tokens: int) -> float:
        """估算成本"""
        prices = self.TOKEN_PRICES.get(self.config.model)
        if not prices:
            return 0.0
        
        # 假设输入输出token比例约为1:1
        input_cost = (tokens / 2) * prices["input"] / 1000
        output_cost = (tokens / 2) * prices["output"] / 1000
        return input_cost + output_cost
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算实际成本"""
        prices = self.TOKEN_PRICES.get(self.config.model)
        if not prices:
            return 0.0
        
        input_cost = input_tokens * prices["input"] / 1000
        output_cost = output_tokens * prices["output"] / 1000
        return input_cost + output_cost


class AnthropicService(BaseLLMService):
    """Anthropic Claude服务实现"""
    
    # Token价格 (USD per 1K tokens)
    TOKEN_PRICES = {
        ModelType.CLAUDE_3_HAIKU: {"input": 0.00025, "output": 0.00125},
        ModelType.CLAUDE_3_SONNET: {"input": 0.003, "output": 0.015},
        ModelType.CLAUDE_3_OPUS: {"input": 0.015, "output": 0.075},
    }
    
    def __init__(self, api_key: str, config: ModelConfig):
        super().__init__(api_key, config)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """调用Anthropic API"""
        start_time = time.time()
        
        try:
            # 转换消息格式，Anthropic只支持system + user消息交替
            system_message = ""
            user_messages = []
            
            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                elif msg.role == "user":
                    user_messages.append(msg.content)
                elif msg.role == "assistant":
                    # Anthropic不支持assistant消息，跳过
                    continue
            
            # 合并用户消息
            user_content = "\n\n".join(user_messages)
            
            # 调用API
            response = await self.client.messages.create(
                model=self.config.model.value,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_message if system_message else None,
                messages=[
                    {"role": "user", "content": user_content}
                ],
                timeout=self.config.timeout,
                **kwargs
            )
            
            # 计算统计信息
            latency = time.time() - start_time
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # 计算成本
            cost = self._calculate_cost(
                response.usage.input_tokens,
                response.usage.output_tokens
            )
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"Anthropic API调用失败: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        try:
            # 使用anthropic的tokenizer
            return self.client.count_tokens(text)
        except:
            # 简单估算
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_words = len(text.split()) - chinese_chars
            return int(chinese_chars * 1.5 + english_words * 1.2)
    
    def estimate_cost(self, tokens: int) -> float:
        """估算成本"""
        prices = self.TOKEN_PRICES.get(self.config.model)
        if not prices:
            return 0.0
        
        # 假设输入输出token比例约为3:1
        input_cost = (tokens * 0.75) * prices["input"] / 1000
        output_cost = (tokens * 0.25) * prices["output"] / 1000
        return input_cost + output_cost
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算实际成本"""
        prices = self.TOKEN_PRICES.get(self.config.model)
        if not prices:
            return 0.0
        
        input_cost = input_tokens * prices["input"] / 1000
        output_cost = output_tokens * prices["output"] / 1000
        return input_cost + output_cost


class GLMService(BaseLLMService):
    """GLM服务实现，使用OpenAI兼容接口"""
    
    # Token价格 (USD per 1K tokens) - 估算值
    TOKEN_PRICES = {
        ModelType.GLM_4_FLASH: {"input": 0.0005, "output": 0.002},
        ModelType.GLM_4_AIR: {"input": 0.001, "output": 0.003},
        ModelType.GLM_4_VISION: {"input": 0.002, "output": 0.006},
    }
    
    def __init__(self, api_key: str, config: ModelConfig, base_url: str = "https://open.bigmodel.cn/api/paas/v4"):
        super().__init__(api_key, config)
        self.base_url = base_url
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """调用GLM API（OpenAI兼容接口）"""
        start_time = time.time()
        
        try:
            # 转换消息格式
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # 调用API
            response = await self.client.chat.completions.create(
                model=self.config.model.value,
                messages=openai_messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                timeout=self.config.timeout,
                **kwargs
            )
            
            # 计算统计信息
            latency = time.time() - start_time
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # 估算成本
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)
            
            return LLMResponse(
                content=content,
                model_used=self.config.model.value,
                tokens_used=tokens_used,
                cost=cost,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"GLM API调用失败: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        try:
            import tiktoken
            # GLM使用类似GPT的tokenization
            encoding = tiktoken.encoding_for_model("gpt-4")
            return len(encoding.encode(text))
        except ImportError:
            # 简单估算：中文字符算2个token，英文单词算1.3个token
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            english_words = len(text.split()) - chinese_chars
            return int(chinese_chars * 2 + english_words * 1.3)
    
    def estimate_cost(self, tokens: int) -> float:
        """估算成本"""
        prices = self.TOKEN_PRICES.get(self.config.model)
        if not prices:
            return 0.0
        
        # 假设输入输出token比例约为1:1
        input_cost = (tokens / 2) * prices["input"] / 1000
        output_cost = (tokens / 2) * prices["output"] / 1000
        return input_cost + output_cost
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算实际成本"""
        prices = self.TOKEN_PRICES.get(self.config.model)
        if not prices:
            return 0.0
        
        input_cost = input_tokens * prices["input"] / 1000
        output_cost = output_tokens * prices["output"] / 1000
        return input_cost + output_cost


class LLMServiceFactory:
    """LLM服务工厂"""
    
    @staticmethod
    def create_service(provider: LLMProvider, api_key: str, config: ModelConfig, **kwargs) -> BaseLLMService:
        """创建LLM服务实例"""
        if provider == LLMProvider.OPENAI:
            return OpenAIService(api_key, config)
        elif provider == LLMProvider.ANTHROPIC:
            return AnthropicService(api_key, config)
        elif provider == LLMProvider.GLM:
            base_url = kwargs.get('base_url', 'https://open.bigmodel.cn/api/paas/v4')
            return GLMService(api_key, config, base_url)
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")


class LLMServiceManager:
    """LLM服务管理器"""
    
    def __init__(self):
        self.services: Dict[str, BaseLLMService] = {}
        self.default_service: Optional[str] = None
    
    def add_service(self, name: str, service: BaseLLMService, is_default: bool = False):
        """添加服务"""
        self.services[name] = service
        if is_default or self.default_service is None:
            self.default_service = name
    
    def get_service(self, name: Optional[str] = None) -> BaseLLMService:
        """获取服务"""
        if name is None:
            name = self.default_service
        
        if name not in self.services:
            raise ValueError(f"服务 '{name}' 不存在")
        
        return self.services[name]
    
    async def chat(self, messages: List[LLMMessage], service_name: Optional[str] = None, **kwargs) -> LLMResponse:
        """聊天接口"""
        service = self.get_service(service_name)
        return await service.chat(messages, **kwargs)
    
    def count_tokens(self, text: str, service_name: Optional[str] = None) -> int:
        """计算token数量"""
        service = self.get_service(service_name)
        return service.count_tokens(text)
    
    def estimate_cost(self, tokens: int, service_name: Optional[str] = None) -> float:
        """估算成本"""
        service = self.get_service(service_name)
        return service.estimate_cost(tokens)
    
    def get_available_services(self) -> List[str]:
        """获取可用服务列表"""
        return list(self.services.keys())