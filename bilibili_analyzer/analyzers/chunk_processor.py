"""
分块处理器
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging

from .text_preprocessor import TextChunk

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """分块配置"""
    max_tokens: int = 2000
    min_tokens: int = 100
    overlap_tokens: int = 200
    max_sentences: int = 50
    respect_sentence_boundaries: bool = True
    semantic_chunking: bool = True


class ChunkProcessor:
    """分块处理器"""
    
    def __init__(self, config: ChunkConfig = None):
        self.config = config or ChunkConfig()
        self.token_counter = self._get_token_counter()
    
    def _get_token_counter(self):
        """获取token计数器"""
        try:
            import tiktoken
            return tiktoken.encoding_for_model("gpt-3.5-turbo")
        except ImportError:
            # 简单的token计数器
            return SimpleTokenCounter()
    
    def count_tokens(self, text: str) -> int:
        """计算token数量"""
        return self.token_counter.encode(text)
    
    def chunk_text(self, text: str, token_counter = None) -> List[TextChunk]:
        """分块处理文本"""
        if token_counter:
            self.token_counter = token_counter
        
        if self.config.semantic_chunking:
            return self._semantic_chunking(text)
        else:
            return self._simple_chunking(text)
    
    def _semantic_chunking(self, text: str) -> List[TextChunk]:
        """语义分块"""
        # 首先按句子分割
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        start_index = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)
            
            # 如果单个句子超过最大token限制，强制分割
            if sentence_tokens > self.config.max_tokens:
                # 处理当前chunk
                if current_chunk:
                    chunk_content = ''.join(current_chunk)
                    chunks.append(TextChunk(
                        content=chunk_content,
                        start_index=start_index,
                        end_index=start_index + len(chunk_content)
                    ))
                    current_chunk = []
                    current_tokens = 0
                    start_index += len(chunk_content)
                
                # 分割长句子
                sub_chunks = self._split_long_sentence(sentence)
                for sub_chunk in sub_chunks:
                    chunks.append(TextChunk(
                        content=sub_chunk,
                        start_index=start_index,
                        end_index=start_index + len(sub_chunk)
                    ))
                    start_index += len(sub_chunk)
                
                continue
            
            # 检查是否可以添加到当前chunk
            if current_tokens + sentence_tokens <= self.config.max_tokens:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            else:
                # 保存当前chunk
                if current_chunk:
                    chunk_content = ''.join(current_chunk)
                    chunks.append(TextChunk(
                        content=chunk_content,
                        start_index=start_index,
                        end_index=start_index + len(chunk_content)
                    ))
                    start_index += len(chunk_content)
                
                # 开始新的chunk
                current_chunk = [sentence]
                current_tokens = sentence_tokens
        
        # 处理最后一个chunk
        if current_chunk:
            chunk_content = ''.join(current_chunk)
            chunks.append(TextChunk(
                content=chunk_content,
                start_index=start_index,
                end_index=start_index + len(chunk_content)
            ))
        
        # 添加重叠区域
        if self.config.overlap_tokens > 0:
            chunks = self._add_overlap(chunks)
        
        return chunks
    
    def _simple_chunking(self, text: str) -> List[TextChunk]:
        """简单分块"""
        chunks = []
        current_position = 0
        
        while current_position < len(text):
            # 计算剩余文本
            remaining_text = text[current_position:]
            
            # 如果剩余文本少于最小token数，直接添加
            if self.count_tokens(remaining_text) <= self.config.max_tokens:
                chunks.append(TextChunk(
                    content=remaining_text,
                    start_index=current_position,
                    end_index=len(text)
                ))
                break
            
            # 寻找合适的分割点
            chunk_end = current_position + self.config.max_tokens * 3  # 粗略估计字符数
            
            # 确保不超过文本长度
            chunk_end = min(chunk_end, len(text))
            
            # 如果尊重句子边界，寻找最近的句子结束符
            if self.config.respect_sentence_boundaries:
                # 寻找句号、感叹号、问号
                sentence_end = self._find_sentence_end(text, chunk_end)
                if sentence_end > current_position + self.config.min_tokens * 3:
                    chunk_end = sentence_end
            
            # 提取chunk
            chunk_content = text[current_position:chunk_end]
            chunks.append(TextChunk(
                content=chunk_content,
                start_index=current_position,
                end_index=chunk_end
            ))
            
            current_position = chunk_end
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """分割句子"""
        # 使用正则表达式分割句子，保持标点符号
        sentences = re.split(r'([。！？\n])', text)
        
        # 重新组合句子和标点
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        # 过滤空句子
        return [s.strip() for s in combined_sentences if s.strip()]
    
    def _find_sentence_end(self, text: str, position: int) -> int:
        """寻找句子结束位置"""
        # 向前寻找最近的句子结束符
        search_start = max(0, position - 500)  # 最多向前搜索500字符
        substring = text[search_start:position]
        
        # 寻找所有句子结束符
        matches = list(re.finditer(r'[。！？\n]', substring))
        
        if matches:
            # 返回最后一个句子结束符的位置
            last_match = matches[-1]
            return search_start + last_match.end()
        
        # 如果没有找到，返回原始位置
        return position
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """分割长句子"""
        tokens = self.count_tokens(sentence)
        if tokens <= self.config.max_tokens:
            return [sentence]
        
        # 按字符数大致分割
        target_chars = int(len(sentence) * self.config.max_tokens / tokens)
        chunks = []
        
        for i in range(0, len(sentence), target_chars):
            chunk = sentence[i:i + target_chars]
            chunks.append(chunk)
        
        return chunks
    
    def _add_overlap(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """添加重叠区域"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            if i == 0:
                # 第一个chunk不添加重叠
                overlapped_chunks.append(chunk)
            else:
                # 计算重叠内容
                prev_chunk = chunks[i - 1]
                overlap_start = max(0, len(prev_chunk.content) - self.config.overlap_tokens * 3)
                overlap_content = prev_chunk.content[overlap_start:]
                
                # 创建新的chunk
                new_content = overlap_content + chunk.content
                overlapped_chunk = TextChunk(
                    content=new_content,
                    start_index=prev_chunk.start_index + overlap_start,
                    end_index=chunk.end_index
                )
                overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def optimize_chunks(self, chunks: List[TextChunk]) -> List[TextChunk]:
        """优化分块"""
        optimized = []
        
        for chunk in chunks:
            # 移除过短的chunk
            if self.count_tokens(chunk.content) < self.config.min_tokens:
                if optimized:
                    # 合并到前一个chunk
                    optimized[-1].content += chunk.content
                    optimized[-1].end_index = chunk.end_index
                continue
            
            optimized.append(chunk)
        
        return optimized


class SimpleTokenCounter:
    """简单的token计数器"""
    
    def encode(self, text: str) -> int:
        """计算token数量"""
        # 简单估算：中文字符算2个token，英文单词算1.3个token
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_words = len(text.split()) - chinese_chars
        return int(chinese_chars * 2 + english_words * 1.3)