from enum import Enum
from typing import Optional

from fastapi import Query


class PersonRoleEnum(str, Enum):
    """Варианты фильтрации"""
    actor: str = 'actor'
    director: str = 'director'
    writer: str = 'writer'


class Filter:
    """Добавление фильтрации в параметры запроса"""

    def __init__(
        self,
        _filter: Optional[PersonRoleEnum] = Query(
            None,
            title='Фильтрация',
            description='Фильтрует по роли персонажа',
            alias='filter[role]')
    ) -> None:
        self.filter = _filter
