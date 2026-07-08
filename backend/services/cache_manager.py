"""
缓存管理模块

提供图片生成结果和评估结果的缓存功能，减少重复计算
"""
import hashlib
import json
from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import logging
import pickle

logger = logging.getLogger(__name__)


class CacheManager:
    """
    缓存管理器
    
    支持:
    - 内存缓存 (LRU)
    - 磁盘缓存
    - TTL 过期策略
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_memory_items: int = 100,
        default_ttl_hours: int = 24
    ):
        self.cache_dir = cache_dir or Path("./cache")
        self.max_memory_items = max_memory_items
        self.default_ttl = timedelta(hours=default_ttl_hours)
        
        # 内存缓存 (LRU 字典)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_order: list = []
        
        # 确保缓存目录存在
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "data").mkdir(exist_ok=True)
        
        logger.info(f"Cache manager initialized: {self.cache_dir.absolute()}")
    
    def _generate_key(self, *args, **kwargs) -> str:
        """根据参数生成缓存键"""
        key_data = json.dumps({
            "args": args,
            "kwargs": kwargs
        }, sort_keys=True, default=str)
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在或已过期则返回 None
        """
        # 先检查内存缓存
        if key in self._memory_cache:
            cache_entry = self._memory_cache[key]
            
            # 检查是否过期
            if datetime.now() < cache_entry["expires_at"]:
                # 更新访问顺序 (LRU)
                self._cache_order.remove(key)
                self._cache_order.append(key)
                return cache_entry["data"]
            else:
                # 已过期，删除
                del self._memory_cache[key]
                self._cache_order.remove(key)
        
        # 检查磁盘缓存
        cache_file = self.cache_dir / "data" / f"{key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    cache_entry = pickle.load(f)
                
                # 检查是否过期
                if datetime.now() < cache_entry["expires_at"]:
                    # 加载到内存缓存
                    self._add_to_memory_cache(key, cache_entry["data"], cache_entry["ttl"])
                    return cache_entry["data"]
                else:
                    # 已过期，删除文件
                    cache_file.unlink()
                    logger.debug(f"Cache expired: {key}")
                    
            except Exception as e:
                logger.warning(f"Failed to load cache file {key}: {e}")
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None
    ) -> None:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            value: 要缓存的数据
            ttl: 过期时间，默认使用 default_ttl
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + ttl
        
        cache_entry = {
            "data": value,
            "expires_at": expires_at,
            "ttl": ttl,
            "created_at": datetime.now()
        }
        
        # 添加到内存缓存
        self._add_to_memory_cache(key, cache_entry)
        
        # 同时写入磁盘缓存
        self._write_to_disk(key, cache_entry)
    
    def _add_to_memory_cache(self, key: str, entry: Dict[str, Any]) -> None:
        """添加到内存缓存，实现 LRU 策略"""
        # 如果已存在，先删除旧的位置
        if key in self._cache_order:
            self._cache_order.remove(key)
        
        # 添加新的
        self._memory_cache[key] = entry
        self._cache_order.append(key)
        
        # 如果超出最大数量，删除最旧的
        while len(self._cache_order) > self.max_memory_items:
            oldest_key = self._cache_order.pop(0)
            del self._memory_cache[oldest_key]
    
    def _write_to_disk(self, key: str, entry: Dict[str, Any]) -> None:
        """写入磁盘缓存"""
        try:
            cache_file = self.cache_dir / "data" / f"{key}.pkl"
            with open(cache_file, "wb") as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.warning(f"Failed to write cache to disk: {e}")
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功删除
        """
        deleted = False
        
        # 从内存缓存删除
        if key in self._memory_cache:
            del self._memory_cache[key]
            self._cache_order.remove(key)
            deleted = True
        
        # 从磁盘缓存删除
        cache_file = self.cache_dir / "data" / f"{key}.pkl"
        if cache_file.exists():
            cache_file.unlink()
            deleted = True
        
        return deleted
    
    def clear(self) -> int:
        """
        清空所有缓存
        
        Returns:
            删除的缓存数量
        """
        count = len(self._memory_cache)
        
        # 清空内存缓存
        self._memory_cache.clear()
        self._cache_order.clear()
        
        # 清空磁盘缓存
        cache_dir = self.cache_dir / "data"
        if cache_dir.exists():
            for file in cache_dir.glob("*.pkl"):
                file.unlink()
                count += 1
        
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def cleanup_expired(self) -> int:
        """
        清理过期的缓存
        
        Returns:
            清理的数量
        """
        count = 0
        now = datetime.now()
        
        # 清理内存缓存
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if now >= entry["expires_at"]
        ]
        
        for key in expired_keys:
            del self._memory_cache[key]
            self._cache_order.remove(key)
            count += 1
        
        # 清理磁盘缓存
        cache_dir = self.cache_dir / "data"
        if cache_dir.exists():
            for file in cache_dir.glob("*.pkl"):
                try:
                    with open(file, "rb") as f:
                        entry = pickle.load(f)
                    
                    if now >= entry["expires_at"]:
                        file.unlink()
                        count += 1
                except Exception:
                    file.unlink(missing_ok=True)
                    count += 1
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_size = len(self._memory_cache)
        
        disk_count = 0
        disk_size = 0
        cache_dir = self.cache_dir / "data"
        if cache_dir.exists():
            for file in cache_dir.glob("*.pkl"):
                disk_count += 1
                disk_size += file.stat().st_size
        
        return {
            "memory_entries": memory_size,
            "disk_entries": disk_count,
            "disk_size_bytes": disk_size,
            "disk_size_mb": round(disk_size / 1024 / 1024, 2),
            "max_memory_entries": self.max_memory_items,
            "default_ttl_hours": self.default_ttl.total_seconds() / 3600
        }


# 全局缓存实例
cache_manager = CacheManager()


def cached(ttl_hours: int = 24):
    """
    缓存装饰器
    
    用于缓存函数结果
    
    Args:
        ttl_hours: 缓存过期时间 (小时)
        
    Example:
        @cached(ttl_hours=12)
        async def generate_image(prompt, style):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key = cache_manager._generate_key(func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {func.__name__} - {key[:8]}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存入缓存
            ttl = timedelta(hours=ttl_hours)
            cache_manager.set(key, result, ttl)
            logger.debug(f"Cache miss, stored: {func.__name__} - {key[:8]}")
            
            return result
        
        return wrapper
    return decorator
