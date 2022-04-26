import backoff
from elasticsearch import AsyncElasticsearch, ConnectionError

from .storage import AbstractStorage


class ElasticStorage(AbstractStorage):
    @classmethod
    async def create(cls, hosts):
        self = ElasticStorage()
        self.client = AsyncElasticsearch(hosts=hosts)
        return self

    def __init__(self):
        self.client: AsyncElasticsearch = None

    @backoff.on_exception(backoff.expo, ConnectionError, max_tries=10)
    async def get(self, index: str, id: str) -> dict:
        return await self.client.get(index, id)

    @backoff.on_exception(backoff.expo, ConnectionError, max_tries=10)
    async def search(self, **query) -> dict:
        return await self.client.search(**query)

    async def close(self) -> None:
        await self.client.close()
