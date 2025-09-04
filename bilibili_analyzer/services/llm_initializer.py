"""
LLM服务初始化模块
负责根据配置文件初始化各种LLM服务
"""

import os
from typing import Dict, Any, Optional
import logging

from .llm import (
    LLMProvider, ModelType, ModelConfig, LLMServiceFactory, 
    LLMServiceManager, LLMMessage
)
from ..config.analysis_config import LLM_CONFIG

logger = logging.getLogger(__name__)


class LLMServiceInitializer:
    """LLM服务初始化器"""
    
    def __init__(self):
        self.service_manager = LLMServiceManager()
        self.initialized = False
    
    def initialize_services(self) -> LLMServiceManager:
        """根据配置初始化所有LLM服务"""
        if self.initialized:
            return self.service_manager
        
        # 初始化OpenAI服务
        self._initialize_openai_service()
        
        # 初始化Anthropic服务
        self._initialize_anthropic_service()
        
        # 初始化GLM服务
        self._initialize_glm_service()
        
        self.initialized = True
        logger.info("LLM服务初始化完成")
        return self.service_manager
    
    def _initialize_openai_service(self):
        """初始化OpenAI服务"""
        config = LLM_CONFIG.get("openai", {})
        api_key = config.get("api_key")
        
        if not api_key:
            logger.warning("OpenAI API密钥未配置，跳过OpenAI服务初始化")
            return
        
        try:
            # 获取默认模型配置
            default_model = config.get("default_model", "gpt-3.5-turbo")
            model_config_dict = config.get("models", {}).get(default_model, {})
            
            # 创建模型配置
            model_config = ModelConfig(
                provider=LLMProvider.OPENAI,
                model=ModelType(default_model),
                max_tokens=model_config_dict.get("max_tokens", 4000),
                temperature=model_config_dict.get("temperature", 0.7),
                top_p=model_config_dict.get("top_p", 1.0),
                timeout=model_config_dict.get("timeout", 30)
            )
            
            # 创建服务
            service = LLMServiceFactory.create_service(
                LLMProvider.OPENAI, 
                api_key, 
                model_config
            )
            
            # 添加到管理器
            self.service_manager.add_service("openai", service, is_default=True)
            logger.info(f"OpenAI服务初始化成功，默认模型: {default_model}")
            
        except Exception as e:
            logger.error(f"OpenAI服务初始化失败: {e}")
    
    def _initialize_anthropic_service(self):
        """初始化Anthropic服务"""
        config = LLM_CONFIG.get("anthropic", {})
        api_key = config.get("api_key")
        
        if not api_key:
            logger.warning("Anthropic API密钥未配置，跳过Anthropic服务初始化")
            return
        
        try:
            # 获取默认模型配置
            default_model = config.get("default_model", "claude-3-haiku-20240307")
            model_config_dict = config.get("models", {}).get(default_model, {})
            
            # 创建模型配置
            model_config = ModelConfig(
                provider=LLMProvider.ANTHROPIC,
                model=ModelType(default_model),
                max_tokens=model_config_dict.get("max_tokens", 4000),
                temperature=model_config_dict.get("temperature", 0.7),
                top_p=model_config_dict.get("top_p", 1.0),
                timeout=model_config_dict.get("timeout", 30)
            )
            
            # 创建服务
            service = LLMServiceFactory.create_service(
                LLMProvider.ANTHROPIC, 
                api_key, 
                model_config
            )
            
            # 添加到管理器
            self.service_manager.add_service("anthropic", service)
            logger.info(f"Anthropic服务初始化成功，默认模型: {default_model}")
            
        except Exception as e:
            logger.error(f"Anthropic服务初始化失败: {e}")
    
    def _initialize_glm_service(self):
        """初始化GLM服务"""
        config = LLM_CONFIG.get("glm", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://open.bigmodel.cn/api/paas/v4")
        
        if not api_key:
            logger.warning("GLM API密钥未配置，跳过GLM服务初始化")
            return
        
        try:
            # 获取默认模型配置
            default_model = config.get("default_model", "glm-4-flash")
            model_config_dict = config.get("models", {}).get(default_model, {})
            
            # 创建模型配置
            model_config = ModelConfig(
                provider=LLMProvider.GLM,
                model=ModelType(default_model),
                max_tokens=model_config_dict.get("max_tokens", 4000),
                temperature=model_config_dict.get("temperature", 0.7),
                top_p=model_config_dict.get("top_p", 1.0),
                timeout=model_config_dict.get("timeout", 30)
            )
            
            # 创建服务
            service = LLMServiceFactory.create_service(
                LLMProvider.GLM, 
                api_key, 
                model_config,
                base_url=base_url
            )
            
            # 添加到管理器
            self.service_manager.add_service("glm", service)
            logger.info(f"GLM服务初始化成功，默认模型: {default_model}")
            
        except Exception as e:
            logger.error(f"GLM服务初始化失败: {e}")
    
    def get_service_manager(self) -> LLMServiceManager:
        """获取服务管理器"""
        if not self.initialized:
            return self.initialize_services()
        return self.service_manager
    
    def get_available_services(self) -> Dict[str, Any]:
        """获取可用服务信息"""
        if not self.initialized:
            self.initialize_services()
        
        services = {}
        for name in self.service_manager.get_available_services():
            service = self.service_manager.get_service(name)
            services[name] = {
                "provider": service.config.provider.value,
                "model": service.config.model.value,
                "max_tokens": service.config.max_tokens,
                "temperature": service.config.temperature
            }
        
        return services


# 全局LLM服务初始化器实例
llm_initializer = LLMServiceInitializer()


def get_llm_service_manager() -> LLMServiceManager:
    """获取LLM服务管理器（全局函数）"""
    return llm_initializer.get_service_manager()


def get_available_llm_services() -> Dict[str, Any]:
    """获取可用LLM服务信息（全局函数）"""
    return llm_initializer.get_available_services()


async def test_llm_services():
    """测试所有LLM服务"""
    service_manager = get_llm_service_manager()
    available_services = service_manager.get_available_services()
    
    if not available_services:
        print("没有可用的LLM服务")
        return
    
    print("=== LLM服务测试 ===")
    
    # 测试消息
    test_messages = [
        LLMMessage(role="system", content="你是一个测试助手"),
        LLMMessage(role="user", content="请回复'测试成功'来验证服务正常工作")
    ]
    
    for service_name in available_services:
        try:
            print(f"\n测试 {service_name} 服务...")
            
            response = await service_manager.chat(test_messages, service_name)
            
            print(f"✅ {service_name} 测试成功")
            print(f"   模型: {response.model_used}")
            print(f"   响应: {response.content[:100]}...")
            print(f"   Token使用: {response.tokens_used}")
            print(f"   成本: ${response.cost:.4f}")
            print(f"   延迟: {response.latency:.2f}s")
            
        except Exception as e:
            print(f"❌ {service_name} 测试失败: {e}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    # 测试初始化
    import asyncio
    
    async def main():
        # 初始化服务
        service_manager = get_llm_service_manager()
        
        # 打印可用服务
        services = get_available_llm_services()
        print("可用LLM服务:")
        for name, info in services.items():
            print(f"  {name}: {info['provider']} - {info['model']}")
        
        # 测试服务
        await test_llm_services()
    
    asyncio.run(main())