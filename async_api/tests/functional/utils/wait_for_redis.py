import asyncio
import logging
import os

import backoff
from aioredis import create_redis_pool

REDIS_HOST: str = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))


@backoff.on_exception(backoff.expo, ConnectionRefusedError, max_tries=20)
async def main():
    redis = await create_redis_pool(
            (REDIS_HOST, REDIS_PORT),
            minsize=10,
            maxsize=20
        )
    if redis:
        redis.close()

if __name__ == '__main__':
    logger = logging.getLogger('backoff')
    logger.addHandler(logging.StreamHandler())
    asyncio.run(main())
    logger.info('Сервис Redis доступен')
