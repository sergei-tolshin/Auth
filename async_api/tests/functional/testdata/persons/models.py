from typing import List, Optional

from functional.testdata.base import OrjsonMixin, PaginationMixin


class PersonModel(OrjsonMixin):
    """Модель ответа API для персонажей"""
    id: str
    full_name: str
    roles: Optional[List[str]]
    film_ids: Optional[List[str]]


class PersonDetailsModel(PersonModel):
    """Модель ответа API для одного персонажа"""
    actor_film_ids: Optional[List[str]]
    director_film_ids: Optional[List[str]]
    writer_film_ids: Optional[List[str]]


class PersonPagination(PaginationMixin):
    """Модель ответа API для результатов в пагинации"""
    results: List[PersonModel] = []
