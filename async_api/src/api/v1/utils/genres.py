from enum import Enum

from fastapi import Query


class GenreSortEnum(str, Enum):
    """Варианты сортировки"""
    name_asc: str = 'name'
    name_desc: str = '-name'


class Sort:
    """Добавление сортировки в параметры запроса"""

    def __init__(
        self,
        sort: GenreSortEnum = Query(
            GenreSortEnum.name_asc,
            title='Сортировка',
            description='Сортирует по возрастанию и убыванию',
            alias='sort',
        ),
    ) -> None:
        self.sort = (sort,)
