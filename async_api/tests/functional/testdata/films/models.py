from typing import List, Optional

from functional.testdata.base import OrjsonMixin, PaginationMixin


class FilmModel(OrjsonMixin):
    """Модель ответа API для фильмов"""
    id: str
    title: str
    imdb_rating: Optional[float]


class FilmDetailsModel(FilmModel):
    """Модель ответа API для фильмов"""
    film_type: Optional[str]
    description: Optional[str] = None
    genre: Optional[List]
    directors: Optional[List] = None
    actors: Optional[List] = None
    writers: Optional[List] = None


class FilmPagination(PaginationMixin):
    """Модель ответа API для результатов в пагинации"""
    results: List[FilmModel] = []
