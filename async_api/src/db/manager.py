from typing import Optional

import orjson
from elasticsearch import NotFoundError

from db.cache import get_cache
from db.storage import get_storage


class DataManager:

    @classmethod
    async def get(cls, id: str) -> Optional[dict]:
        storage = await get_storage()
        cache = await get_cache()
        # Пытаемся получить данные из кеша, потому что оно работает быстрее
        key = await cache.get_key(cls.index, id)
        instance = await cache.get(key) or None
        if not instance:
            # Если экземпляра нет в кеше, то ищем его в базе
            try:
                doc = await storage.get(cls.index, id)
                if not doc:
                    # Если он отсутствует в базе, значит,
                    # экземпляра вообще нет в базе
                    return None
                # Сохраняем экземпляр в кеш
                instance = doc['_source']
                await cache.set(key, orjson.dumps(instance))
                return instance
            except NotFoundError:
                return None
        return orjson.loads(instance)

    @classmethod
    async def search(cls, **query):
        storage = await get_storage()
        cache = await get_cache()
        print(query)
        key = await cache.get_key(cls.index, query)
        queryset = await cache.get(key) or None
        if not queryset:
            try:
                docs = await storage.search(**query)
                await cache.set(key, orjson.dumps(docs))
                return docs
            except NotFoundError:
                return None
        return orjson.loads(queryset)
