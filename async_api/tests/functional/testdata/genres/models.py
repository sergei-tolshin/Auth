from typing import List, Optional

from functional.testdata.base import OrjsonMixin, PaginationMixin


class GenreModel(OrjsonMixin):
    """Модель ответа API для жанров"""
    id: str
    name: str


class GenreDetailsModel(GenreModel):
    """Модель ответа API подробная"""
    description: Optional[str]


class GenrePagination(PaginationMixin):
    """Модель ответа API для результатов в пагинации"""
    results: List[GenreModel] = []
