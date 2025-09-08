"""
缓存管理模块
"""

import json
import time
import hashlib
import pickle
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_access: float = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()


class CacheConfig:
    """缓存配置"""
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: int = 3600,
                 cleanup_interval: int = 300,
                 enable_compression: bool = True,
                 enable_stats: bool = True):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self.enable_compression = enable_compression
        self.enable_stats = enable_stats


class MemoryCache:
    """内存缓存"""
    
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }
        self.last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 定期清理过期缓存
        self._periodic_cleanup()
        
        entry = self.cache.get(key)
        if entry is None:
            self.stats['misses'] += 1
            return None
        
        # 检查是否过期
        if entry.is_expired():
            self._delete_entry(key)
            self.stats['misses'] += 1
            return None
        
        # 更新访问信息
        entry.update_access()
        self.stats['hits'] += 1
        
        return self._deserialize(entry.value)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        # 检查缓存大小
        if len(self.cache) >= self.config.max_size:
            self._evict_lru()
        
        # 序列化值
        serialized_value = self._serialize(value)
        
        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            value=serialized_value,
            created_at=time.time(),
            ttl=ttl or self.config.default_ttl
        )
        
        self.cache[key] = entry
        self.stats['sets'] += 1
        
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self.cache:
            self._delete_entry(key)
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        entry = self.cache.get(key)
        if entry is None:
            return False
        
        if entry.is_expired():
            self._delete_entry(key)
            return False
        
        return True
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.stats['deletes'] += len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.config.max_size,
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'evictions': self.stats['evictions']
        }
    
    def get_keys(self) -> List[str]:
        """获取所有键"""
        return list(self.cache.keys())
    
    def cleanup(self):
        """清理过期缓存"""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._delete_entry(key)
        
        logger.info(f"清理了 {len(expired_keys)} 个过期缓存项")
    
    def _serialize(self, value: Any) -> Any:
        """序列化值"""
        if self.config.enable_compression:
            try:
                return pickle.dumps(value)
            except (pickle.PicklingError, TypeError) as e:
                logger.warning(f"序列化失败，返回原始值: {e}")
                return value
        return value
    
    def _deserialize(self, value: Any) -> Any:
        """反序列化值"""
        if self.config.enable_compression and isinstance(value, bytes):
            try:
                return pickle.loads(value)
            except (pickle.UnpicklingError, EOFError) as e:
                logger.warning(f"反序列化失败，返回原始值: {e}")
                return value
        return value
    
    def _delete_entry(self, key: str):
        """删除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            self.stats['deletes'] += 1
    
    def _evict_lru(self):
        """淘汰最近最少使用的缓存"""
        if not self.cache:
            return
        
        # 找到最近最少使用的条目
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].last_access)
        
        self._delete_entry(lru_key)
        self.stats['evictions'] += 1
        logger.debug(f"淘汰缓存条目: {lru_key}")
    
    def _periodic_cleanup(self):
        """定期清理"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.config.cleanup_interval:
            self.cleanup()
            self.last_cleanup = current_time


class AnalysisCache:
    """分析结果专用缓存"""
    
    def __init__(self, cache: MemoryCache):
        self.cache = cache
    
    def _generate_key(self, content: str, model: str, task_type: str) -> str:
        """生成缓存键"""
        key_data = f"{content}:{model}:{task_type}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_analysis_result(self, content: str, model: str) -> Optional[Dict[str, Any]]:
        """获取分析结果"""
        key = self._generate_key(content, model, "analysis")
        return self.cache.get(key)
    
    def set_analysis_result(self, content: str, model: str, result: Dict[str, Any], ttl: int = 3600) -> bool:
        """设置分析结果"""
        key = self._generate_key(content, model, "analysis")
        return self.cache.set(key, result, ttl)
    
    def get_summary(self, content: str, model: str) -> Optional[str]:
        """获取总结"""
        key = self._generate_key(content, model, "summary")
        return self.cache.get(key)
    
    def set_summary(self, content: str, model: str, summary: str, ttl: int = 3600) -> bool:
        """设置总结"""
        key = self._generate_key(content, model, "summary")
        return self.cache.set(key, summary, ttl)
    
    def get_key_points(self, content: str, model: str) -> Optional[List[str]]:
        """获取关键点"""
        key = self._generate_key(content, model, "key_points")
        return self.cache.get(key)
    
    def set_key_points(self, content: str, model: str, key_points: List[str], ttl: int = 3600) -> bool:
        """设置关键点"""
        key = self._generate_key(content, model, "key_points")
        return self.cache.set(key, key_points, ttl)
    
    def get_categories(self, content: str, model: str) -> Optional[List[str]]:
        """获取分类"""
        key = self._generate_key(content, model, "categories")
        return self.cache.get(key)
    
    def set_categories(self, content: str, model: str, categories: List[str], ttl: int = 3600) -> bool:
        """设置分类"""
        key = self._generate_key(content, model, "categories")
        return self.cache.set(key, categories, ttl)
    
    def get_tags(self, content: str, model: str) -> Optional[List[str]]:
        """获取标签"""
        key = self._generate_key(content, model, "tags")
        return self.cache.get(key)
    
    def set_tags(self, content: str, model: str, tags: List[str], ttl: int = 3600) -> bool:
        """设置标签"""
        key = self._generate_key(content, model, "tags")
        return self.cache.set(key, tags, ttl)
    
    def clear_analysis_cache(self):
        """清空分析缓存"""
        keys = self.cache.get_keys()
        for key in keys:
            if "analysis" in key or "summary" in key or "key_points" in key or "categories" in key or "tags" in key:
                self.cache.delete(key)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: CacheConfig = None):
        self.memory_cache = MemoryCache(config)
        self.analysis_cache = AnalysisCache(self.memory_cache)
    
    def get_memory_cache(self) -> MemoryCache:
        """获取内存缓存"""
        return self.memory_cache
    
    def get_analysis_cache(self) -> AnalysisCache:
        """获取分析缓存"""
        return self.analysis_cache
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.memory_cache.get_stats()
    
    def cleanup(self):
        """清理所有缓存"""
        self.memory_cache.cleanup()
    
    def clear_all(self):
        """清空所有缓存"""
        self.memory_cache.clear()


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取全局缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def init_cache_manager(config: CacheConfig = None):
    """初始化全局缓存管理器"""
    global _cache_manager
    _cache_manager = CacheManager(config)
    return _cache_manager