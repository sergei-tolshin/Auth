from typing import Optional

from core import config
from fastapi import Query
from pydantic import BaseModel


class Pagination(BaseModel):
    """Модель ответа API с пагинацией"""
    count: int
    total_pages: int
    next: Optional[str] = None
    previous: Optional[str] = None


class Paginator:
    """Добавление пагинации в параметры запроса"""

    def __init__(
        self,
        page_number: int = Query(
            None,
            title='Номер страницы',
            description='Номер страницы',
            alias='page[number]',
            ge=1),
        page_size: int = Query(
            None,
            title='Количество результатов на странице',
            description='Количество результатов на странице',
            alias='page[size]',
            ge=1,
            le=config.MAX_PAGE_SIZE),
    ) -> None:
        self.page_number = page_number or 1
        self.page_size = page_size or config.PAGE_SIZE


class SearchQuery:
    """Добавление поиска в параметры запроса"""

    def __init__(self, query: str = Query(
        ...,
        min_length=3,
        title='Слово или фраза',
        description='Слово или фраза')
    ) -> None:
        self.search_text = query
