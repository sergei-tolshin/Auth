from typing import Optional
from uuid import UUID

from models.base import ESBaseModel, OrjsonMixin


class GenresElasticModel(ESBaseModel):
    name: str
    description: Optional[str] = None


class GenresResponseModel(OrjsonMixin):
    """Модель ответа API для жанров"""
    id: UUID
    name: str


class GenresDetailsResponseModel(GenresResponseModel):
    """Модель ответа API подробная"""
    description: Optional[str]
