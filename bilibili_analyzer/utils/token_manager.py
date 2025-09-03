"""
Token管理和成本控制模块
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TokenLimitType(Enum):
    """Token限制类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TOTAL = "total"


@dataclass
class TokenUsage:
    """Token使用记录"""
    timestamp: float
    tokens: int
    cost: float
    model: str
    task_type: str
    content_hash: str


@dataclass
class TokenLimit:
    """Token限制配置"""
    limit_type: TokenLimitType
    max_tokens: int
    max_cost: float
    reset_interval: int  # 重置间隔（秒）


@dataclass
class TokenStats:
    """Token统计信息"""
    total_tokens: int
    total_cost: float
    usage_by_model: Dict[str, Dict[str, Any]]
    usage_by_task: Dict[str, Dict[str, Any]]
    daily_usage: List[TokenUsage]
    current_period_start: float
    current_period_end: float


class TokenManager:
    """Token管理器"""
    
    def __init__(self, 
                 daily_token_limit: int = 100000,
                 daily_cost_limit: float = 10.0,
                 weekly_token_limit: int = 500000,
                 weekly_cost_limit: float = 50.0,
                 monthly_token_limit: int = 2000000,
                 monthly_cost_limit: float = 200.0):
        
        self.limits = {
            TokenLimitType.DAILY: TokenLimit(
                TokenLimitType.DAILY, daily_token_limit, daily_cost_limit, 86400
            ),
            TokenLimitType.WEEKLY: TokenLimit(
                TokenLimitType.WEEKLY, weekly_token_limit, weekly_cost_limit, 604800
            ),
            TokenLimitType.MONTHLY: TokenLimit(
                TokenLimitType.MONTHLY, monthly_token_limit, monthly_cost_limit, 2592000
            )
        }
        
        self.usage_history: List[TokenUsage] = []
        self.model_stats: Dict[str, Dict[str, Any]] = {}
        self.task_stats: Dict[str, Dict[str, Any]] = {}
        
        # 加载历史数据
        self._load_usage_data()
    
    def _load_usage_data(self):
        """加载使用数据"""
        # 这里可以从数据库或文件加载历史数据
        # 现在使用内存存储
        pass
    
    def _save_usage_data(self):
        """保存使用数据"""
        # 这里可以保存到数据库或文件
        pass
    
    def record_usage(self, tokens: int, cost: float, model: str, task_type: str, content: str = ""):
        """记录Token使用"""
        usage = TokenUsage(
            timestamp=time.time(),
            tokens=tokens,
            cost=cost,
            model=model,
            task_type=task_type,
            content_hash=self._hash_content(content)
        )
        
        self.usage_history.append(usage)
        
        # 更新模型统计
        if model not in self.model_stats:
            self.model_stats[model] = {
                'total_tokens': 0,
                'total_cost': 0,
                'usage_count': 0
            }
        
        self.model_stats[model]['total_tokens'] += tokens
        self.model_stats[model]['total_cost'] += cost
        self.model_stats[model]['usage_count'] += 1
        
        # 更新任务统计
        if task_type not in self.task_stats:
            self.task_stats[task_type] = {
                'total_tokens': 0,
                'total_cost': 0,
                'usage_count': 0
            }
        
        self.task_stats[task_type]['total_tokens'] += tokens
        self.task_stats[task_type]['total_cost'] += cost
        self.task_stats[task_type]['usage_count'] += 1
        
        # 清理旧数据
        self._cleanup_old_data()
        
        # 保存数据
        self._save_usage_data()
        
        logger.info(f"记录Token使用: {tokens} tokens, ${cost:.4f}, 模型: {model}, 任务: {task_type}")
    
    def check_limit(self, tokens: int, cost: float, limit_type: TokenLimitType = TokenLimitType.DAILY) -> bool:
        """检查是否超过限制"""
        limit = self.limits[limit_type]
        
        # 计算当前周期的使用量
        current_usage = self._get_period_usage(limit_type)
        
        # 检查token限制
        if current_usage['tokens'] + tokens > limit.max_tokens:
            logger.warning(f"Token限制超限: {current_usage['tokens'] + tokens} > {limit.max_tokens}")
            return False
        
        # 检查成本限制
        if current_usage['cost'] + cost > limit.max_cost:
            logger.warning(f"成本限制超限: ${current_usage['cost'] + cost:.4f} > ${limit.max_cost:.4f}")
            return False
        
        return True
    
    def get_usage_stats(self, limit_type: TokenLimitType = TokenLimitType.DAILY) -> TokenStats:
        """获取使用统计"""
        current_usage = self._get_period_usage(limit_type)
        limit = self.limits[limit_type]
        
        # 计算周期时间
        now = time.time()
        period_start = now - (now % limit.reset_interval)
        period_end = period_start + limit.reset_interval
        
        # 获取周期内的使用记录
        period_usage = [
            usage for usage in self.usage_history
            if period_start <= usage.timestamp < period_end
        ]
        
        return TokenStats(
            total_tokens=current_usage['tokens'],
            total_cost=current_usage['cost'],
            usage_by_model=self.model_stats,
            usage_by_task=self.task_stats,
            daily_usage=period_usage,
            current_period_start=period_start,
            current_period_end=period_end
        )
    
    def get_limit_status(self, limit_type: TokenLimitType = TokenLimitType.DAILY) -> Dict[str, Any]:
        """获取限制状态"""
        stats = self.get_usage_stats(limit_type)
        limit = self.limits[limit_type]
        
        return {
            'limit_type': limit_type.value,
            'max_tokens': limit.max_tokens,
            'max_cost': limit.max_cost,
            'used_tokens': stats.total_tokens,
            'used_cost': stats.total_cost,
            'remaining_tokens': limit.max_tokens - stats.total_tokens,
            'remaining_cost': limit.max_cost - stats.total_cost,
            'token_usage_rate': stats.total_tokens / limit.max_tokens,
            'cost_usage_rate': stats.total_cost / limit.max_cost,
            'period_start': stats.current_period_start,
            'period_end': stats.current_period_end,
            'time_remaining': stats.current_period_end - time.time()
        }
    
    def _get_period_usage(self, limit_type: TokenLimitType) -> Dict[str, Union[int, float]]:
        """获取周期使用量"""
        limit = self.limits[limit_type]
        now = time.time()
        period_start = now - (now % limit.reset_interval)
        
        # 筛选周期内的使用记录
        period_usage = [
            usage for usage in self.usage_history
            if period_start <= usage.timestamp < now
        ]
        
        return {
            'tokens': sum(usage.tokens for usage in period_usage),
            'cost': sum(usage.cost for usage in period_usage)
        }
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        # 保留最近30天的数据
        cutoff_time = time.time() - (30 * 86400)
        self.usage_history = [
            usage for usage in self.usage_history
            if usage.timestamp >= cutoff_time
        ]
    
    def _hash_content(self, content: str) -> str:
        """生成内容哈希"""
        import hashlib
        return hashlib.md5(content.encode()).hexdigest()
    
    def reset_limits(self, limit_type: TokenLimitType = None):
        """重置限制"""
        if limit_type:
            # 重置特定限制
            limit = self.limits[limit_type]
            now = time.time()
            period_start = now - (now % limit.reset_interval)
            
            # 删除周期内的使用记录
            self.usage_history = [
                usage for usage in self.usage_history
                if usage.timestamp < period_start
            ]
        else:
            # 重置所有限制
            self.usage_history.clear()
            self.model_stats.clear()
            self.task_stats.clear()
        
        self._save_usage_data()
        logger.info(f"已重置 {limit_type.value if limit_type else '所有'} 限制")
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """估算成本"""
        # 简单的成本估算
        model_costs = {
            'gpt-3.5-turbo': 0.002,  # $0.002 per 1K tokens
            'gpt-4': 0.06,          # $0.06 per 1K tokens
            'gpt-4-turbo': 0.03,     # $0.03 per 1K tokens
            'gpt-4o': 0.015,         # $0.015 per 1K tokens
            'claude-3-haiku': 0.00025,  # $0.00025 per 1K tokens
            'claude-3-sonnet': 0.003,    # $0.003 per 1K tokens
            'claude-3-opus': 0.015,       # $0.015 per 1K tokens
        }
        
        cost_per_1k = model_costs.get(model, 0.01)
        return (tokens / 1000) * cost_per_1k
    
    def get_model_recommendation(self, tokens: int, budget: float) -> str:
        """获取模型推荐"""
        models = [
            ('gpt-3.5-turbo', 0.002),
            ('claude-3-haiku', 0.00025),
            ('gpt-4o', 0.015),
            ('claude-3-sonnet', 0.003),
            ('gpt-4-turbo', 0.03),
            ('gpt-4', 0.06),
            ('claude-3-opus', 0.015),
        ]
        
        for model, cost_per_1k in models:
            estimated_cost = (tokens / 1000) * cost_per_1k
            if estimated_cost <= budget:
                return model
        
        return 'gpt-3.5-turbo'  # 默认最便宜的模型


class CostAnalyzer:
    """成本分析器"""
    
    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager
    
    def analyze_cost_efficiency(self, task_type: str) -> Dict[str, Any]:
        """分析成本效率"""
        stats = self.token_manager.get_usage_stats()
        
        if task_type not in stats.usage_by_task:
            return {'error': f'未找到任务类型: {task_type}'}
        
        task_stats = stats.usage_by_task[task_type]
        
        return {
            'task_type': task_type,
            'total_tokens': task_stats['total_tokens'],
            'total_cost': task_stats['total_cost'],
            'usage_count': task_stats['usage_count'],
            'avg_tokens_per_task': task_stats['total_tokens'] / task_stats['usage_count'],
            'avg_cost_per_task': task_stats['total_cost'] / task_stats['usage_count'],
            'cost_per_token': task_stats['total_cost'] / task_stats['total_tokens'],
            'efficiency_score': self._calculate_efficiency_score(task_stats)
        }
    
    def _calculate_efficiency_score(self, task_stats: Dict[str, Any]) -> float:
        """计算效率分数"""
        # 简单的效率计算：成本越低，效率越高
        avg_cost_per_token = task_stats['total_cost'] / task_stats['total_tokens']
        
        # 基准效率分数（假设每token成本为0.00001时效率为100）
        baseline_cost = 0.00001
        efficiency_score = max(0, min(100, (baseline_cost / avg_cost_per_token) * 100))
        
        return efficiency_score
    
    def get_cost_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取成本优化建议"""
        suggestions = []
        
        # 分析各模型的使用情况
        for model, stats in self.token_manager.model_stats.items():
            avg_cost_per_token = stats['total_cost'] / stats['total_tokens']
            
            # 如果成本过高，建议更换模型
            if avg_cost_per_token > 0.0001:  # 每1000token成本超过$0.1
                suggestions.append({
                    'type': 'model_optimization',
                    'model': model,
                    'current_cost_per_token': avg_cost_per_token,
                    'suggestion': f'考虑使用更便宜的模型替代 {model}',
                    'potential_savings': self._estimate_savings(model, avg_cost_per_token)
                })
        
        # 分析任务类型的使用情况
        for task_type, stats in self.token_manager.task_stats.items():
            if stats['usage_count'] > 10:  # 使用频繁的任务
                avg_cost_per_task = stats['total_cost'] / stats['usage_count']
                
                if avg_cost_per_task > 1.0:  # 每次任务成本超过$1
                    suggestions.append({
                        'type': 'task_optimization',
                        'task_type': task_type,
                        'current_cost_per_task': avg_cost_per_task,
                        'suggestion': f'考虑优化 {task_type} 任务的实现，减少API调用',
                        'potential_savings': self._estimate_task_savings(task_type, avg_cost_per_task)
                    })
        
        return suggestions
    
    def _estimate_savings(self, model: str, current_cost: float) -> float:
        """估算节省金额"""
        # 简单的节省估算
        cheaper_models = {
            'gpt-4': 0.015,      # 建议使用gpt-4o
            'gpt-4-turbo': 0.015, # 建议使用gpt-4o
            'claude-3-opus': 0.003, # 建议使用claude-3-sonnet
        }
        
        if model in cheaper_models:
            new_cost = cheaper_models[model]
            return (current_cost - new_cost) * self.token_manager.model_stats[model]['total_tokens']
        
        return 0.0
    
    def _estimate_task_savings(self, task_type: str, current_cost: float) -> float:
        """估算任务节省金额"""
        # 假设优化后可以减少30%的成本
        return current_cost * 0.3 * self.token_manager.task_stats[task_type]['usage_count']


# 全局Token管理器实例
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """获取全局Token管理器"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager


def init_token_manager(config: Dict[str, Any] = None):
    """初始化全局Token管理器"""
    global _token_manager
    if config:
        _token_manager = TokenManager(**config)
    else:
        _token_manager = TokenManager()
    return _token_manager