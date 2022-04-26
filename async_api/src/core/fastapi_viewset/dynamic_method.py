from core import config
from core.fastapi_viewset.schemas import Paginator
from fastapi import Depends, Path, Request

from .schemas import SearchQuery


class MethodFactory:

    @classmethod
    def make_retrieve(cls, key_name, key_type):
        async def retrieve(
                cls,
                request: Request,
                param: key_type = Path(..., alias=key_name),
        ):
            entity = await cls.retrieve_function(cls.model, id=param)
            return entity
        return retrieve

    @classmethod
    def make_retrieve_list(cls, filter, sort):
        async def retrieve_list(
            cls,
            request: Request,
            *,
            filter: filter = Depends(),
            sort: sort = Depends(),
            paginator: Paginator = Depends(),
        ):
            params = dict(request.query_params)
            query = await cls.get_query(params)
            count = await cls.count(query)
            data = [hit['_source'] for hit in query['hits']['hits']]
            total, next, previous = await cls.get_pages(
                request, count, len(data),
                paginator.page_number, paginator.page_size
            )
            return cls.prepare_response(count, total, next, previous, data)
        return retrieve_list

    @classmethod
    def make_retrieve_search(cls):
        async def retrieve_search(
            cls,
            request: Request,
            *,
            query: SearchQuery = Depends(),
            paginator: Paginator = Depends(),
        ):
            params = dict(request.query_params)
            query = await cls.get_query(params)
            count = await cls.count(query)
            data = [hit['_source'] for hit in query['hits']['hits']]
            total, next, previous = await cls.get_pages(
                request, count, len(data),
                paginator.page_number, paginator.page_size
            )
            return cls.prepare_response(count, total, next, previous, data)
        return retrieve_search

    @classmethod
    def make_retrieve_relation(cls, key_name, key_type, index):
        async def retrieve_relation(
                cls,
                request: Request,
                param: key_type = Path(..., alias=key_name),
                paginator: Paginator = Depends(),
        ):
            entity = await cls.retrieve_function(cls.model, id=param)
            params = dict(request.query_params)
            params['_index'] = config.ELASTIC_INDEX[index]
            params['body'] = {'query': {'ids': {'values': entity['film_ids']}}}
            query = await cls.get_query(params)
            count = await cls.count(query)
            data = [hit['_source'] for hit in query['hits']['hits']]
            total, next, previous = await cls.get_pages(
                request, count, len(data),
                paginator.page_number, paginator.page_size
            )
            return cls.prepare_response(count, total, next, previous, data)
        return retrieve_relation
