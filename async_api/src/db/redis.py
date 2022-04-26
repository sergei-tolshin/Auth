from hashlib import sha256
from typing import Optional, Union

import backoff
import orjson
from aioredis import Redis, RedisError, create_redis_pool
from core import config

from db.cache import AbstractCache


class RedisCache(AbstractCache):
    @classmethod
    @backoff.on_exception(backoff.expo, ConnectionRefusedError, max_tries=10)
    async def create(cls, address, minsize=10, maxsize=20):
        self = RedisCache()
        self.redis = await create_redis_pool(
            address,
            minsize=minsize,
            maxsize=maxsize
        )
        return self

    def __init__(self):
        self.redis: Redis = None

    @backoff.on_exception(backoff.expo, RedisError, max_tries=10)
    async def set(self, key: str, data: Union[str, bytes]) -> None:
        await self.redis.set(key, data, expire=config.CACHE_EXPIRE_IN_SECONDS)

    @backoff.on_exception(backoff.expo, RedisError, max_tries=10)
    async def get(self, key: str) -> Optional[bytes]:
        return await self.redis.get(key) or None

    async def get_key(self, prefix: str, query: Union[str, dict]) -> str:
        str_params: bytes = orjson.dumps(query)
        _hash = sha256(str_params).hexdigest()
        return f'{prefix}:{_hash}'

    async def close(self) -> None:
        await self.redis.close()
