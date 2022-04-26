from abc import ABC, abstractclassmethod
from typing import List, Optional

from .utils import RequestParams


class AbstractService(ABC):
    @property
    def index(self):
        raise NotImplementedError

    @property
    def model(self):
        raise NotImplementedError

    @property
    def search_fields(self):
        raise NotImplementedError

    @abstractclassmethod
    async def get_query(self, params):
        pass


class BaseService(AbstractService):
    search_fields: Optional[List] = []

    @classmethod
    async def get_query(cls, params):
        request_params = RequestParams()
        query = await request_params.get_query(params, cls.index,
                                               cls.search_fields)
        return query
