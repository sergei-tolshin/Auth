from typing import List, Optional

from db.model import BaseManager, BaseModel, PostgresBaseModel
from utils.mixins import UUIDMixin


class PersonBaseManager(BaseManager):
    def instances(self, ids):
        if not ids:
            return None

        condition = f"IN {tuple(ids)}" if len(ids) > 1 else f"= '{ids[0]}'"
        query = f"""
            SELECT
                p.id as p_id,
                p.full_name,
                pfw.role as role,
                fw.id as film
            FROM person p
            LEFT JOIN person_film_work pfw ON pfw.person_id = p.id
            LEFT JOIN film_work fw ON fw.id = pfw.film_work_id
            WHERE p.id {condition};
        """

        return self._model_objects(query=query)


class PersonFilmModel(PostgresBaseModel):
    """Модель фильмов где участвуют персонажи"""
    role: Optional[str]


class PersonObjectModel(PostgresBaseModel):
    """Модель персонажей"""


class PersonInstanceModel(UUIDMixin):
    """Модель экземпляров персонажей для ElasticSearch"""
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    film_ids: Optional[List[str]] = None
    actor_film_ids: Optional[List[str]] = None
    director_film_ids: Optional[List[str]] = None
    writer_film_ids: Optional[List[str]] = None


class Person(BaseModel):
    """Основная модель персонажей"""
    table_name = 'person'
    object_model = PersonObjectModel
    instance_model = PersonInstanceModel
    relations = {
        'film': {
            'table': 'person_film_work',
            'field': 'film_work_id',
            'model': PersonFilmModel,
        },
    }
    manager_class = PersonBaseManager
