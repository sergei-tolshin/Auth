from abc import ABC, abstractmethod
from typing import Optional, Union


class AbstractCache(ABC):

    @abstractmethod
    async def set(self, key: str, data: Union[str, bytes]) -> None:
        pass

    @abstractmethod
    async def get(self, key: str) -> Union[str, bytes]:
        pass

    @abstractmethod
    async def get_key(self, prefix: str, query: Union[str, dict]) -> str:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


cache: Optional[AbstractCache] = None


async def get_cache() -> AbstractCache:
    return cache
