from typing import List, Optional

from db.model import BaseManager, BaseModel, PostgresBaseModel
from utils.mixins import UUIDMixin

from apps.genre.models import GenreFilmModel, GenreInstanceModel
from apps.person.models import PersonFilmModel, PersonInstanceModel


class FilmBaseManager(BaseManager):
    def instances(self, ids):
        if not ids:
            return None

        condition = f"IN {tuple(ids)}" if len(ids) > 1 else f"= '{ids[0]}'"
        query = f"""
            SELECT
                fw.id as fw_id,
                fw.title,
                fw.description,
                fw.rating,
                fw.type,
                fw.created,
                fw.modified,
                pfw.role,
                p.id as person_id,
                p.full_name,
                g.id as genre_id,
                g.name as genre
            FROM film_work fw
            LEFT JOIN person_film_work pfw ON pfw.film_work_id = fw.id
            LEFT JOIN person p ON p.id = pfw.person_id
            LEFT JOIN genre_film_work gfw ON gfw.film_work_id = fw.id
            LEFT JOIN genre g ON g.id = gfw.genre_id
            WHERE fw.id {condition};
        """

        return self._model_objects(query=query)


class FilmObjectModel(PostgresBaseModel):
    """Модель фильмов"""


class FilmInstanceModel(UUIDMixin):
    """Модель экземпляров фильмов для ElasticSearch"""
    imdb_rating: Optional[float] = None
    title: str
    description: Optional[str] = None
    film_type: Optional[str] = None
    genre: Optional[List[GenreInstanceModel]] = None
    directors_names: Optional[List[str]] = None
    actors_names: Optional[List[str]] = None
    writers_names: Optional[List[str]] = None
    directors: Optional[List[PersonInstanceModel]] = None
    actors: Optional[List[PersonInstanceModel]] = None
    writers: Optional[List[PersonInstanceModel]] = None


class Film(BaseModel):
    """Основная можель фильмов"""
    table_name = 'film_work'
    object_model = FilmObjectModel
    instance_model = FilmInstanceModel
    relations = {
        'genre': {
            'table': 'genre_film_work',
            'field': 'genre_id',
            'model': GenreFilmModel,
        },
        'person': {
            'table': 'person_film_work',
            'field': 'person_id',
            'model': PersonFilmModel,
        }
    }
    manager_class = FilmBaseManager
