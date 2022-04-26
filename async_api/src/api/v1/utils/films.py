from enum import Enum
from typing import Optional

from fastapi import Query


class FilmSortEnum(str, Enum):
    """Варианты сортировки"""
    imdb_rating_asc: str = 'imdb_rating'
    imdb_rating_desc: str = '-imdb_rating'


class Sort:
    """Добавление сортировки в параметры запроса"""

    def __init__(
        self,
        sort: FilmSortEnum = Query(
            FilmSortEnum.imdb_rating_desc,
            title='Сортировка',
            description='Сортирует по возрастанию и убыванию',
            alias='sort',
        ),
    ) -> None:
        self.sort = (sort,)


class Filter:
    """Добавление фильтрации в параметры запроса"""

    def __init__(
        self,
        _filter: Optional[str] = Query(
            None,
            title='Фильтр',
            description='Фильтрует по жанрам',
            alias='filter[genre]')
    ):
        self.filter = _filter
