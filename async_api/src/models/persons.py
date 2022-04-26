from typing import List, Optional
from uuid import UUID

from models.base import ESBaseModel, OrjsonMixin


class PersonsElasticModel(ESBaseModel):
    full_name: str
    roles: Optional[List[str]] = None
    film_ids: Optional[List[str]] = None
    actor_film_ids: Optional[List[str]] = None
    director_film_ids: Optional[List[str]] = None
    writer_film_ids: Optional[List[str]] = None


class PersonsResponseModel(OrjsonMixin):
    """Модель ответа API для персонажей"""
    id: UUID
    full_name: str
    roles: Optional[List[str]]
    film_ids: Optional[List[str]]


class PersonsDetailsResponseModel(PersonsResponseModel):
    """Модель ответа API для одного персонажа"""
    film_ids: Optional[List[str]]
    actor_film_ids: Optional[List[str]]
    director_film_ids: Optional[List[str]]
    writer_film_ids: Optional[List[str]]
