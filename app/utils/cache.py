from typing import Optional

import redis.asyncio as redis

from app.core.config import settings
from app.core.logger import logger


class CacheClient:
    _redis: Optional[redis.Redis] = None

    @classmethod
    def init(cls):
        """初始化 Redis 连接池"""
        if cls._redis is None:
            cls._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"Redis client initialized: {settings.REDIS_URL}")

    @classmethod
    async def close(cls):
        """关闭连接"""
        if cls._redis:
            await cls._redis.close()
            logger.info("Redis client closed")

    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        """获取缓存，带异常捕获"""
        try:
            if cls._redis:
                return await cls._redis.get(key)
        except Exception as e:
            logger.warning(f"Redis GET error: {e}")
        return None

    @classmethod
    async def set(cls, key: str, value: str, ttl: int = 600):
        """设置缓存，带异常捕获"""
        try:
            if cls._redis:
                await cls._redis.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis SET error: {e}")


# 全局实例
cache = CacheClient()
