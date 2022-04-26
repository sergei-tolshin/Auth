from typing import Optional

from db.model import BaseManager, BaseModel, PostgresBaseModel
from utils.mixins import UUIDMixin


class GenreBaseManager(BaseManager):
    def instances(self, ids):
        if not ids:
            return None

        condition = f"IN {tuple(ids)}" if len(ids) > 1 else f"= '{ids[0]}'"
        query = f"""
            SELECT
                g.id,
                g.name,
                g.description
            FROM genre g
            WHERE g.id {condition};
        """

        return self._model_objects(query=query)


class GenreFilmModel(PostgresBaseModel):
    """Модель фильмов по жанрам"""


class GenreObjectModel(PostgresBaseModel):
    """Модель жанров"""
    name: Optional[str]
    description: Optional[str] = None


class GenreInstanceModel(UUIDMixin):
    """Модель экземпляров жанров для ElasticSearch"""
    name: Optional[str]
    description: Optional[str] = None


class Genre(BaseModel):
    """Базовая модель жанров"""
    table_name = 'genre'
    object_model = GenreObjectModel
    instance_model = GenreInstanceModel
    relations = {
        'film': {
            'table': 'genre_film_work',
            'field': 'film_work_id',
            'model': GenreFilmModel,
        },
    }
    manager_class = GenreBaseManager
