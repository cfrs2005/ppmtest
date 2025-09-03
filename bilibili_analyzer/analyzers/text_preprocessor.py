"""
文本预处理器
"""

import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """文本块"""
    content: str
    start_index: int
    end_index: int
    metadata: Dict[str, Any] = None


class TextPreprocessor:
    """文本预处理器"""
    
    def __init__(self):
        self.clean_patterns = [
            # 移除B站常见的弹幕相关文本
            r'^\d{2}:\d{2}:\d{2}\s*$',  # 时间戳
            r'^\s*$',  # 空行
            r'^[！!]{2,}$',  # 多个感叹号
            r'^[？?]{2,}$',  # 多个问号
            r'^[。.]{2,}$',  # 多个句号
            r'^[哈h]{2,}$',  # 哈哈笑声
            r'^[啊a]{2,}$',  # 啊啊
            r'^[哦o]{2,}$',  # 哦哦
            r'^[呀y]{2,}$',  # 呀呀
            r'^[哇w]{2,}$',  # 哇哇
            r'^[嘻x]{2,}$',  # 嘻嘻
            r'^[笑xiao]{2,}$',  # 笑笑
            r'^[赞zan]{2,}$',  # 赞赞
            r'^[顶ding]{2,}$',  # 顶顶
            r'^[666]{3,}$',  # 666
            r'^[888]{3,}$',  # 888
            r'^[999]{3,}$',  # 999
            r'^[1-9]\d{2}$',  # 三位数字
            r'^[👍👎❤️😂😭🎉🔥💯]+$',  # 纯表情符号
        ]
        
        # 合并模式
        self.merge_patterns = [
            # 合并连续的短句
            (r'([^。！？\n])\n([^。！？\n])', r'\1 \2'),
            # 合并断开的句子
            (r'([^。！？])\n([a-zA-Z])', r'\1 \2'),
            # 合并中文句子
            (r'([^。！？])\n([\u4e00-\u9fff])', r'\1\2'),
        ]
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 检查是否匹配清理模式
            should_remove = False
            for pattern in self.clean_patterns:
                if re.match(pattern, line):
                    should_remove = True
                    break
            
            if not should_remove:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def merge_lines(self, text: str) -> str:
        """合并断行"""
        for pattern, replacement in self.merge_patterns:
            text = re.sub(pattern, replacement, text)
        return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """提取句子"""
        # 使用句号、感叹号、问号分割句子
        sentences = re.split(r'[。！？\n]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def preprocess_subtitle(self, subtitle_content: str, format_type: str = 'json') -> str:
        """预处理字幕内容"""
        try:
            if format_type == 'json':
                # 解析JSON格式的字幕
                data = json.loads(subtitle_content)
                if isinstance(data, dict) and 'body' in data:
                    # 提取字幕文本
                    text_parts = []
                    for item in data['body']:
                        if 'content' in item:
                            text_parts.append(item['content'])
                    text = '\n'.join(text_parts)
                else:
                    text = subtitle_content
            elif format_type == 'srt':
                # 解析SRT格式的字幕
                text = self._parse_srt(subtitle_content)
            else:
                text = subtitle_content
            
            # 清理和合并文本
            text = self.clean_text(text)
            text = self.merge_lines(text)
            
            return text
            
        except Exception as e:
            logger.error(f"字幕预处理失败: {e}")
            return subtitle_content
    
    def _parse_srt(self, srt_content: str) -> str:
        """解析SRT格式字幕"""
        lines = srt_content.split('\n')
        text_parts = []
        
        for line in lines:
            line = line.strip()
            # 跳过序号和时间戳
            if not line or '-->' in line or line.isdigit():
                continue
            text_parts.append(line)
        
        return '\n'.join(text_parts)
    
    def get_text_stats(self, text: str) -> Dict[str, Any]:
        """获取文本统计信息"""
        chars = len(text)
        words = len(text.split())
        sentences = len(self.extract_sentences(text))
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        
        return {
            'total_chars': chars,
            'total_words': words,
            'total_sentences': sentences,
            'chinese_chars': chinese_chars,
            'english_words': english_words,
            'language_ratio': {
                'chinese': chinese_chars / chars if chars > 0 else 0,
                'english': english_words / chars if chars > 0 else 0
            }
        }