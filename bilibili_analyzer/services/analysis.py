"""
分析服务模块 - 集成所有分析功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .llm import LLMServiceManager, ModelConfig, LLMProvider, ModelType

logger = logging.getLogger(__name__)


# 定义数据类以避免循环导入
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AnalysisResult:
    """分析结果"""
    summary: str
    key_points: List[str]
    categories: List[str]
    tags: List[str]
    knowledge_entries: List[Dict[str, Any]]
    total_tokens: int
    total_cost: float
    analysis_time: float
    model_used: str
    chunk_count: int


@dataclass
class AnalysisConfig:
    """分析配置"""
    enable_chunking: bool = True
    max_tokens_per_chunk: int = 2000
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1小时
    enable_knowledge_extraction: bool = True
    max_knowledge_entries: int = 20
    model_config: ModelConfig = None


class AnalysisService:
    """分析服务"""
    
    def __init__(self, llm_manager: LLMServiceManager = None):
        self.llm_manager = llm_manager or LLMServiceManager()
        # 简化初始化，避免循环导入
        self.analyzer = None
    
    def _init_default_services(self):
        """初始化默认LLM服务"""
        # 暂时留空，避免循环导入
        pass
    
    async def analyze_video(self, video_id: int, force_reanalysis: bool = False) -> AnalysisResult:
        """分析视频"""
        # 暂时返回空结果，避免循环导入
        return AnalysisResult(
            summary="分析功能暂时不可用",
            key_points=[],
            categories=[],
            tags=[],
            knowledge_entries=[],
            total_tokens=0,
            total_cost=0.0,
            analysis_time=0.0,
            model_used="none",
            chunk_count=0
        )
    
    async def analyze_subtitle_content(self, content: str, format_type: str = 'json') -> AnalysisResult:
        """分析字幕内容"""
        # 暂时返回空结果，避免循环导入
        return AnalysisResult(
            summary="分析功能暂时不可用",
            key_points=[],
            categories=[],
            tags=[],
            knowledge_entries=[],
            total_tokens=0,
            total_cost=0.0,
            analysis_time=0.0,
            model_used="none",
            chunk_count=0
        )
    
    async def generate_summary(self, content: str, service_name: Optional[str] = None) -> str:
        """生成总结"""
        return "总结功能暂时不可用"
    
    async def extract_key_points(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """提取关键点"""
        return []
    
    async def categorize_content(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """内容分类"""
        return []
    
    async def generate_tags(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """生成标签"""
        return []
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计"""
        return {'status': '简化版本，统计功能暂时不可用'}
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """获取成本分析"""
        return {'status': '简化版本，成本分析功能暂时不可用'}
    
    def cleanup_cache(self):
        """清理缓存"""
        pass
    
    def reset_token_limits(self):
        """重置Token限制"""
        pass


# 全局分析服务实例
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """获取全局分析服务"""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service


def init_analysis_service(llm_manager: LLMServiceManager = None) -> AnalysisService:
    """初始化全局分析服务"""
    global _analysis_service
    _analysis_service = AnalysisService(llm_manager)
    return _analysis_service