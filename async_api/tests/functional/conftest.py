import asyncio
from dataclasses import dataclass

import aiohttp
import aioredis
import pytest
from elasticsearch import AsyncElasticsearch, helpers
from multidict import CIMultiDictProxy
from pydantic import BaseModel

from .settings import config
from .utils.utils import build_url


@dataclass
class HTTPResponse:
    body: dict
    headers: CIMultiDictProxy[str]
    status: int


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts=config.ELASTIC_URL)
    yield client
    await client.close()


@pytest.fixture(scope='session')
async def cache():
    client = await aioredis.create_redis_pool(
        (config.REDIS_HOST, config.REDIS_PORT),
        minsize=10,
        maxsize=20)
    await client.flushdb()
    yield client
    await client.flushdb()
    client.close()
    await client.wait_closed()


@pytest.fixture(scope='session')
async def session():
    session = aiohttp.ClientSession()
    yield session
    await session.close()


@pytest.fixture
def make_get_request(session):
    async def inner(path: str, params: dict = None) -> HTTPResponse:
        params = params or {}
        url = build_url(config.SERVICE_URL, path)
        async with session.get(url, params=params) as response:
            return HTTPResponse(
                body=await response.json(),
                headers=response.headers,
                status=response.status,
            )
    return inner


@pytest.fixture
async def bulk(es_client):

    async def _bulk(index: str,
                    objects: list[BaseModel],
                    op_type: str = 'index'):

        actions = [
            {
                "_index": index,
                "_id": obj.id,
                # default value for op_type 'index',
                # other values may be: [create, delete]
                # for update not working with this query
                "_op_type": op_type,
                "_source": obj.dict()
            }
            for obj in objects
        ]

        await helpers.async_bulk(client=es_client, actions=actions,
                                 raise_on_error=False, stats_only=True,
                                 refresh=True)

    return _bulk
