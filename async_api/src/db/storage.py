from abc import ABC, abstractmethod
from typing import Optional


class AbstractStorage(ABC):
    @abstractmethod
    def get(self, index, id):
        pass

    @abstractmethod
    def search(self, **query):
        pass

    @abstractmethod
    def close(self):
        pass


db: Optional[AbstractStorage] = None


async def get_storage() -> AbstractStorage:
    return db
