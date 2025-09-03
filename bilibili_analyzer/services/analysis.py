"""
分析服务模块 - 集成所有分析功能
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..services import LLMServiceManager, ModelConfig, LLMProvider, ModelType
from ..analyzers import ContentAnalyzer, AnalysisResult, AnalysisConfig
from ..cache import get_cache_manager
from ..utils import get_token_manager, CostAnalyzer
from ..models import Video, Subtitle, Analysis, KnowledgeEntry, db

logger = logging.getLogger(__name__)


class AnalysisService:
    """分析服务"""
    
    def __init__(self, llm_manager: LLMServiceManager = None):
        self.llm_manager = llm_manager or LLMServiceManager()
        self.cache_manager = get_cache_manager()
        self.token_manager = get_token_manager()
        self.cost_analyzer = CostAnalyzer(self.token_manager)
        
        # 初始化分析器
        self.analyzer = ContentAnalyzer(
            self.llm_manager,
            AnalysisConfig(
                enable_chunking=True,
                max_tokens_per_chunk=2000,
                enable_caching=True,
                cache_ttl=3600,
                enable_knowledge_extraction=True
            )
        )
        
        # 初始化默认LLM服务
        self._init_default_services()
    
    def _init_default_services(self):
        """初始化默认LLM服务"""
        # 这里可以从配置文件读取API密钥
        # 现在使用环境变量或配置
        
        # 示例：添加OpenAI服务
        try:
            openai_config = ModelConfig(
                provider=LLMProvider.OPENAI,
                model=ModelType.GPT_3_5_TURBO,
                max_tokens=4000,
                temperature=0.7
            )
            # 需要API密钥
            # openai_service = LLMServiceFactory.create_service(
            #     LLMProvider.OPENAI, 
            #     "your-openai-api-key", 
            #     openai_config
            # )
            # self.llm_manager.add_service("openai-gpt35", openai_service, is_default=True)
        except Exception as e:
            logger.warning(f"OpenAI服务初始化失败: {e}")
        
        # 示例：添加Anthropic服务
        try:
            anthropic_config = ModelConfig(
                provider=LLMProvider.ANTHROPIC,
                model=ModelType.CLAUDE_3_HAIKU,
                max_tokens=4000,
                temperature=0.7
            )
            # 需要API密钥
            # anthropic_service = LLMServiceFactory.create_service(
            #     LLMProvider.ANTHROPIC,
            #     "your-anthropic-api-key",
            #     anthropic_config
            # )
            # self.llm_manager.add_service("anthropic-haiku", anthropic_service)
        except Exception as e:
            logger.warning(f"Anthropic服务初始化失败: {e}")
    
    async def analyze_video(self, video_id: int, force_reanalysis: bool = False) -> AnalysisResult:
        """分析视频"""
        try:
            # 获取视频信息
            video = Video.query.get(video_id)
            if not video:
                raise ValueError(f"视频不存在: {video_id}")
            
            # 检查是否已有分析结果
            if not force_reanalysis:
                existing_analysis = video.get_latest_analysis()
                if existing_analysis:
                    logger.info(f"视频 {video_id} 已有分析结果，跳过分析")
                    return self._convert_to_analysis_result(existing_analysis)
            
            # 获取字幕
            subtitle = video.get_latest_subtitle()
            if not subtitle:
                raise ValueError(f"视频 {video_id} 没有字幕")
            
            logger.info(f"开始分析视频 {video_id}: {video.title}")
            
            # 分析字幕内容
            result = await self.analyzer.analyze_subtitle(
                subtitle.content,
                subtitle.format,
                service_name=self.llm_manager.default_service
            )
            
            # 记录Token使用
            self.token_manager.record_usage(
                result.total_tokens,
                result.total_cost,
                result.model_used,
                "video_analysis",
                subtitle.content[:100]  # 使用内容前100字符作为标识
            )
            
            # 保存分析结果
            analysis = self.analyzer.save_analysis_result(result, video_id, subtitle.id)
            
            logger.info(f"视频分析完成: {video.title}, 分析ID: {analysis.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"视频分析失败: {e}")
            raise
    
    async def analyze_subtitle_content(self, content: str, format_type: str = 'json') -> AnalysisResult:
        """分析字幕内容"""
        try:
            logger.info("开始分析字幕内容")
            
            # 检查Token限制
            estimated_tokens = self._estimate_tokens(content)
            estimated_cost = self.token_manager.estimate_cost(estimated_tokens, "gpt-3.5-turbo")
            
            if not self.token_manager.check_limit(estimated_tokens, estimated_cost):
                raise ValueError("Token使用限制已达到，请稍后再试")
            
            # 分析内容
            result = await self.analyzer.analyze_subtitle(
                content,
                format_type,
                service_name=self.llm_manager.default_service
            )
            
            # 记录Token使用
            self.token_manager.record_usage(
                result.total_tokens,
                result.total_cost,
                result.model_used,
                "subtitle_analysis",
                content[:100]
            )
            
            logger.info(f"字幕内容分析完成，使用了 {result.total_tokens} tokens")
            
            return result
            
        except Exception as e:
            logger.error(f"字幕内容分析失败: {e}")
            raise
    
    async def generate_summary(self, content: str, service_name: Optional[str] = None) -> str:
        """生成总结"""
        try:
            # 检查缓存
            cache_key = f"summary:{hash(content)}"
            cached_result = self.cache_manager.get_analysis_cache().get_summary(
                content, 
                service_name or self.llm_manager.default_service
            )
            
            if cached_result:
                logger.info("使用缓存的总结")
                return cached_result
            
            # 生成总结
            summary = await self.analyzer.generate_summary(content, service_name)
            
            # 缓存结果
            self.cache_manager.get_analysis_cache().set_summary(
                content,
                service_name or self.llm_manager.default_service,
                summary
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"生成总结失败: {e}")
            raise
    
    async def extract_key_points(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """提取关键点"""
        try:
            # 检查缓存
            cached_result = self.cache_manager.get_analysis_cache().get_key_points(
                content,
                service_name or self.llm_manager.default_service
            )
            
            if cached_result:
                logger.info("使用缓存的关键点")
                return cached_result
            
            # 提取关键点
            key_points = await self.analyzer.extract_key_points(content, service_name)
            
            # 缓存结果
            self.cache_manager.get_analysis_cache().set_key_points(
                content,
                service_name or self.llm_manager.default_service,
                key_points
            )
            
            return key_points
            
        except Exception as e:
            logger.error(f"提取关键点失败: {e}")
            raise
    
    async def categorize_content(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """内容分类"""
        try:
            # 检查缓存
            cached_result = self.cache_manager.get_analysis_cache().get_categories(
                content,
                service_name or self.llm_manager.default_service
            )
            
            if cached_result:
                logger.info("使用缓存的分类")
                return cached_result
            
            # 分类内容
            categories = await self.analyzer.categorize_content(content, service_name)
            
            # 缓存结果
            self.cache_manager.get_analysis_cache().set_categories(
                content,
                service_name or self.llm_manager.default_service,
                categories
            )
            
            return categories
            
        except Exception as e:
            logger.error(f"内容分类失败: {e}")
            raise
    
    async def generate_tags(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """生成标签"""
        try:
            # 检查缓存
            cached_result = self.cache_manager.get_analysis_cache().get_tags(
                content,
                service_name or self.llm_manager.default_service
            )
            
            if cached_result:
                logger.info("使用缓存的标签")
                return cached_result
            
            # 生成标签
            tags = await self.analyzer.generate_tags(content, service_name)
            
            # 缓存结果
            self.cache_manager.get_analysis_cache().set_tags(
                content,
                service_name or self.llm_manager.default_service,
                tags
            )
            
            return tags
            
        except Exception as e:
            logger.error(f"生成标签失败: {e}")
            raise
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计"""
        return {
            'cache_stats': self.cache_manager.get_stats(),
            'token_stats': self.token_manager.get_usage_stats(),
            'limit_status': self.token_manager.get_limit_status(),
            'available_services': self.llm_manager.get_available_services()
        }
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """获取成本分析"""
        return {
            'overall_efficiency': self.cost_analyzer.analyze_cost_efficiency('overall'),
            'optimization_suggestions': self.cost_analyzer.get_cost_optimization_suggestions(),
            'model_usage': self.token_manager.model_stats,
            'task_usage': self.token_manager.task_stats
        }
    
    def _estimate_tokens(self, content: str) -> int:
        """估算Token数量"""
        # 简单估算：中文字符算2个token，英文单词算1.3个token
        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
        english_words = len(content.split()) - chinese_chars
        return int(chinese_chars * 2 + english_words * 1.3)
    
    def _convert_to_analysis_result(self, analysis: Analysis) -> AnalysisResult:
        """将数据库分析记录转换为AnalysisResult"""
        return AnalysisResult(
            summary=analysis.summary,
            key_points=analysis.get_key_points(),
            categories=analysis.get_categories(),
            tags=analysis.get_tags(),
            knowledge_entries=[],  # 需要从数据库加载
            total_tokens=0,  # 需要从Token管理器获取
            total_cost=0.0,  # 需要从Token管理器获取
            analysis_time=analysis.analysis_time,
            model_used=analysis.model_used,
            chunk_count=0  # 需要从分析元数据获取
        )
    
    def cleanup_cache(self):
        """清理缓存"""
        self.cache_manager.cleanup()
    
    def reset_token_limits(self):
        """重置Token限制"""
        self.token_manager.reset_limits()


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