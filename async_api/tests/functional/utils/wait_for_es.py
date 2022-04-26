import asyncio
import logging
import os

import backoff
from elasticsearch import AsyncElasticsearch

ELASTIC_HOST = os.getenv('ELASTIC_HOST', '127.0.0.1')
ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))


@backoff.on_exception(backoff.expo, ConnectionRefusedError, max_tries=20)
async def main():
    if not await es_client.ping():
        raise ConnectionRefusedError("Connection to ES failed")
    await es_client.close()

if __name__ == '__main__':
    es_client = AsyncElasticsearch(hosts=f'{ELASTIC_HOST}:{ELASTIC_PORT}')
    logger = logging.getLogger('backoff')
    logger.addHandler(logging.StreamHandler())
    asyncio.run(main())
    logger.info('Сервис Elastic Search доступен')
