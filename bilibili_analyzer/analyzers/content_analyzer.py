"""
内容分析器主类
"""

import json
import time
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from ..services import LLMServiceManager, LLMMessage, ModelConfig, LLMProvider, ModelType
from ..models import Analysis, KnowledgeEntry, get_or_create_tag, db
from .text_preprocessor import TextPreprocessor
from .chunk_processor import ChunkProcessor, ChunkConfig

logger = logging.getLogger(__name__)


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


class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, llm_manager: LLMServiceManager, config: AnalysisConfig = None):
        self.llm_manager = llm_manager
        self.config = config or AnalysisConfig()
        self.text_preprocessor = TextPreprocessor()
        self.chunk_processor = ChunkProcessor(
            ChunkConfig(max_tokens=self.config.max_tokens_per_chunk)
        )
        
        # 缓存字典（生产环境应该使用Redis）
        self.cache = {}
        self.cache_timestamps = {}
    
    async def analyze_subtitle(
        self, 
        subtitle_content: str, 
        subtitle_format: str = 'json',
        service_name: Optional[str] = None
    ) -> AnalysisResult:
        """分析字幕内容"""
        start_time = time.time()
        
        try:
            # 预处理字幕
            logger.info("开始预处理字幕")
            processed_text = self.text_preprocessor.preprocess_subtitle(
                subtitle_content, subtitle_format
            )
            
            # 获取文本统计
            text_stats = self.text_preprocessor.get_text_stats(processed_text)
            logger.info(f"文本统计: {text_stats}")
            
            # 分块处理
            if self.config.enable_chunking:
                chunks = self.chunk_processor.chunk_text(processed_text)
                logger.info(f"分块数量: {len(chunks)}")
            else:
                chunks = [processed_text]
                logger.info("不分块处理")
            
            # 分析各个chunk
            analysis_results = []
            total_tokens = 0
            total_cost = 0
            
            for i, chunk in enumerate(chunks):
                logger.info(f"分析第 {i+1}/{len(chunks)} 个chunk")
                
                chunk_result = await self._analyze_chunk(chunk, service_name)
                analysis_results.append(chunk_result)
                total_tokens += chunk_result.get('tokens_used', 0)
                total_cost += chunk_result.get('cost', 0)
            
            # 合并分析结果
            merged_result = await self._merge_analysis_results(analysis_results)
            
            # 生成最终结果
            analysis_time = time.time() - start_time
            model_used = self.llm_manager.get_service(service_name).config.model.value
            
            result = AnalysisResult(
                summary=merged_result.get('summary', ''),
                key_points=merged_result.get('key_points', []),
                categories=merged_result.get('categories', []),
                tags=merged_result.get('tags', []),
                knowledge_entries=merged_result.get('knowledge_entries', []),
                total_tokens=total_tokens,
                total_cost=total_cost,
                analysis_time=analysis_time,
                model_used=model_used,
                chunk_count=len(chunks)
            )
            
            logger.info(f"分析完成，耗时: {analysis_time:.2f}秒，总token: {total_tokens}，成本: ${total_cost:.4f}")
            
            return result
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            raise
    
    async def _analyze_chunk(self, chunk: Union[str, Any], service_name: Optional[str] = None) -> Dict[str, Any]:
        """分析单个chunk"""
        chunk_content = chunk if isinstance(chunk, str) else chunk.content
        
        # 检查缓存
        cache_key = self._get_cache_key(chunk_content, service_name)
        if self.config.enable_caching and cache_key in self.cache:
            logger.debug("使用缓存结果")
            return self.cache[cache_key]
        
        # 构建分析提示
        messages = self._build_analysis_messages(chunk_content)
        
        # 调用LLM
        response = await self.llm_manager.chat(messages, service_name)
        
        # 解析响应
        try:
            result = json.loads(response.content)
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试修复
            result = self._parse_fallback_response(response.content)
        
        # 添加token和成本信息
        result['tokens_used'] = response.tokens_used
        result['cost'] = response.cost
        
        # 缓存结果
        if self.config.enable_caching:
            self.cache[cache_key] = result
            self.cache_timestamps[cache_key] = time.time()
        
        return result
    
    def _build_analysis_messages(self, text: str) -> List[LLMMessage]:
        """构建分析消息"""
        system_prompt = """你是一个专业的内容分析助手。请分析给定的文本内容，并以JSON格式返回分析结果。

返回格式必须包含以下字段：
- summary: 内容总结（100-200字）
- key_points: 关键点列表（5-10个要点）
- categories: 内容分类列表（如：技术、教育、娱乐等）
- tags: 标签列表（10-15个相关标签）
- knowledge_entries: 知识条目列表，每个条目包含：
  - title: 知识条目标题
  - content: 详细内容
  - type: 知识类型（concept/fact/method/tip）
  - importance: 重要性等级（1-5）

请确保：
1. 总结简洁明了，抓住核心内容
2. 关键点具有代表性和信息量
3. 分类准确反映内容主题
4. 标签覆盖主要关键词
5. 知识条目结构化、实用性强"""

        user_prompt = f"请分析以下内容：\n\n{text}"
        
        return [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt)
        ]
    
    async def _merge_analysis_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个分析结果"""
        if len(results) == 1:
            return results[0]
        
        # 构建合并提示
        all_summaries = [r.get('summary', '') for r in results]
        all_key_points = []
        all_categories = set()
        all_tags = set()
        all_knowledge_entries = []
        
        # 收集所有数据
        for result in results:
            all_key_points.extend(result.get('key_points', []))
            all_categories.update(result.get('categories', []))
            all_tags.update(result.get('tags', []))
            all_knowledge_entries.extend(result.get('knowledge_entries', []))
        
        # 如果启用了知识提取且条目过多，进行筛选
        if self.config.enable_knowledge_extraction:
            all_knowledge_entries = self._filter_knowledge_entries(all_knowledge_entries)
        
        # 合并总结
        merged_summary = await self._merge_summaries(all_summaries)
        
        # 去重和排序关键点
        unique_key_points = self._deduplicate_key_points(all_key_points)
        
        return {
            'summary': merged_summary,
            'key_points': unique_key_points[:10],  # 限制数量
            'categories': list(all_categories)[:5],  # 限制数量
            'tags': list(all_tags)[:15],  # 限制数量
            'knowledge_entries': all_knowledge_entries[:self.config.max_knowledge_entries]
        }
    
    async def _merge_summaries(self, summaries: List[str]) -> str:
        """合并多个总结"""
        if len(summaries) == 1:
            return summaries[0]
        
        # 构建合并提示
        prompt = f"""请将以下多个总结合并为一个连贯的总结：

总结列表：
{chr(10).join(f"{i+1}. {summary}" for i, summary in enumerate(summaries))}

要求：
1. 保持核心信息完整
2. 消除重复内容
3. 逻辑连贯，结构清晰
4. 控制在200-300字之间
5. 直接返回合并后的总结，不要添加其他内容"""

        messages = [
            LLMMessage(role="system", content="你是一个专业的文本合并助手，擅长整合多个文本的核心信息。"),
            LLMMessage(role="user", content=prompt)
        ]
        
        try:
            response = await self.llm_manager.chat(messages)
            return response.content
        except Exception as e:
            logger.error(f"合并总结失败: {e}")
            # 返回第一个总结作为fallback
            return summaries[0]
    
    def _deduplicate_key_points(self, key_points: List[str]) -> List[str]:
        """去重关键点"""
        unique_points = []
        seen = set()
        
        for point in key_points:
            # 简单的重复检测
            key = point.lower().strip()
            if key not in seen and len(key) > 10:  # 过滤过短的点
                unique_points.append(point)
                seen.add(key)
        
        return unique_points
    
    def _filter_knowledge_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """筛选知识条目"""
        # 按重要性排序
        filtered = []
        for entry in entries:
            importance = entry.get('importance', 1)
            if importance >= 3:  # 只保留重要性3以上的条目
                filtered.append(entry)
        
        # 按重要性排序
        filtered.sort(key=lambda x: x.get('importance', 1), reverse=True)
        
        return filtered
    
    def _parse_fallback_response(self, response: str) -> Dict[str, Any]:
        """解析失败时的备用处理"""
        logger.warning("JSON解析失败，使用备用解析")
        
        # 简单的文本分割
        lines = response.split('\n')
        
        result = {
            'summary': '',
            'key_points': [],
            'categories': [],
            'tags': [],
            'knowledge_entries': []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 尝试识别各个部分
            if '总结' in line or 'summary' in line.lower():
                current_section = 'summary'
            elif '关键点' in line or 'key' in line.lower():
                current_section = 'key_points'
            elif '分类' in line or 'category' in line.lower():
                current_section = 'categories'
            elif '标签' in line or 'tag' in line.lower():
                current_section = 'tags'
            elif current_section and line.startswith('-'):
                content = line[1:].strip()
                if current_section == 'key_points':
                    result['key_points'].append(content)
                elif current_section == 'categories':
                    result['categories'].append(content)
                elif current_section == 'tags':
                    result['tags'].append(content)
            elif current_section == 'summary' and not result['summary']:
                result['summary'] = line
        
        return result
    
    def _get_cache_key(self, text: str, service_name: Optional[str] = None) -> str:
        """生成缓存键"""
        import hashlib
        content = f"{text}:{service_name or 'default'}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def cleanup_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.config.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            del self.cache_timestamps[key]
        
        logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    async def generate_summary(self, content: str, service_name: Optional[str] = None) -> str:
        """生成总结"""
        messages = [
            LLMMessage(role="system", content="你是一个专业的内容总结助手。请为给定的文本生成一个简洁明了的总结（100-200字）。"),
            LLMMessage(role="user", content=f"请总结以下内容：\n\n{content}")
        ]
        
        response = await self.llm_manager.chat(messages, service_name)
        return response.content
    
    async def extract_key_points(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """提取关键点"""
        messages = [
            LLMMessage(role="system", content="你是一个专业的内容分析助手。请从给定的文本中提取5-10个关键点，每个关键点应该简洁明了，包含重要信息。"),
            LLMMessage(role="user", content=f"请提取以下内容的关键点：\n\n{content}")
        ]
        
        response = await self.llm_manager.chat(messages, service_name)
        
        # 解析关键点列表
        try:
            data = json.loads(response.content)
            return data.get('key_points', [])
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            # JSON解析失败时使用简单的行解析
            logger.warning(f"关键点JSON解析失败，使用行解析: {e}")
            lines = response.split('\n')
            key_points = []
            for line in lines:
                line = line.strip()
                if line.startswith('-') or line.startswith('•'):
                    key_points.append(line[1:].strip())
            return key_points
    
    async def categorize_content(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """内容分类"""
        messages = [
            LLMMessage(role="system", content="你是一个专业的内容分类助手。请为给定的文本内容进行分类，返回3-5个最相关的分类标签。"),
            LLMMessage(role="user", content=f"请分类以下内容：\n\n{content}")
        ]
        
        response = await self.llm_manager.chat(messages, service_name)
        
        # 解析分类列表
        try:
            data = json.loads(response.content)
            return data.get('categories', [])
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            # JSON解析失败时使用简单的行解析
            logger.warning(f"分类JSON解析失败，使用行解析: {e}")
            lines = response.split('\n')
            categories = []
            for line in lines:
                line = line.strip()
                if line:
                    categories.append(line)
            return categories[:5]
    
    async def generate_tags(self, content: str, service_name: Optional[str] = None) -> List[str]:
        """生成标签"""
        messages = [
            LLMMessage(role="system", content="你是一个专业的标签生成助手。请为给定的文本内容生成10-15个相关标签，标签应该简洁、准确、具有代表性。"),
            LLMMessage(role="user", content=f"请为以下内容生成标签：\n\n{content}")
        ]
        
        response = await self.llm_manager.chat(messages, service_name)
        
        # 解析标签列表
        try:
            data = json.loads(response.content)
            return data.get('tags', [])
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            # JSON解析失败时使用简单的行解析
            logger.warning(f"标签JSON解析失败，使用行解析: {e}")
            lines = response.split('\n')
            tags = []
            for line in lines:
                line = line.strip()
                if line:
                    tags.append(line)
            return tags[:15]
    
    def build_knowledge_base(self, analysis_result: AnalysisResult) -> List[KnowledgeEntry]:
        """构建知识库条目"""
        knowledge_entries = []
        
        for entry_data in analysis_result.knowledge_entries:
            try:
                entry = KnowledgeEntry(
                    title=entry_data.get('title', ''),
                    content=entry_data.get('content', ''),
                    knowledge_type=entry_data.get('type', 'concept'),
                    importance=entry_data.get('importance', 1)
                )
                
                # 添加标签
                tags = entry_data.get('tags', [])
                for tag_name in tags:
                    entry.add_tag(tag_name)
                
                knowledge_entries.append(entry)
                
            except Exception as e:
                logger.error(f"创建知识条目失败: {e}")
        
        return knowledge_entries
    
    def save_analysis_result(self, analysis_result: AnalysisResult, video_id: int, subtitle_id: int) -> Analysis:
        """保存分析结果到数据库"""
        try:
            # 创建分析记录
            analysis = Analysis(
                video_id=video_id,
                subtitle_id=subtitle_id,
                summary=analysis_result.summary,
                analysis_time=analysis_result.analysis_time,
                model_used=analysis_result.model_used
            )
            
            # 设置分析数据
            analysis.set_key_points(analysis_result.key_points)
            analysis.set_categories(analysis_result.categories)
            analysis.set_tags(analysis_result.tags)
            
            # 保存到数据库
            db.session.add(analysis)
            db.session.flush()  # 获取ID
            
            # 创建知识条目
            if self.config.enable_knowledge_extraction:
                knowledge_entries = self.build_knowledge_base(analysis_result)
                for entry in knowledge_entries:
                    entry.analysis_id = analysis.id
                    db.session.add(entry)
            
            db.session.commit()
            logger.info(f"分析结果已保存到数据库，ID: {analysis.id}")
            
            return analysis
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"保存分析结果失败: {e}")
            raise