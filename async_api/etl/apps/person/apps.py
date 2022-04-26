import logging
from typing import Optional

from services.apps import BaseApps

from .models import Person
from .schema import SCHEMA as person_schema

logger = logging.getLogger(__name__)


class PersonApps(BaseApps):
    index = 'persons'
    schema = person_schema

    def __init__(self, state, es_client, *args, **kwargs):
        super().__init__(state, es_client, *args, **kwargs)
        self.relations = self._get_relations()

    def _get_relations(self):
        return Person.objects.relations

    def run(self):
        if persons := self.extract():
            logger.info('Extracted %d modified Persons', len(persons))
            self.states['modified'] = f'{persons[-1].modified}'
            ids = [person.id for person in persons]
            instanses = Person.objects.instances(ids)
            transformed_data = self.transform(instanses)

            """Если есть связанные объекты, то обновляем их"""
            if self.relations:
                for relation in self.relations:
                    self._update_relation(relation, 'person', ids)

            logger.info('Start Persons data transfer to Elasticsearch')
            inserter = self.load(index=self.index, schema=self.schema)
            for _ in transformed_data:
                inserter.send(_)
            inserter.close()

            logger.info('Save Persons state of data modified')
            self.save_state()
        else:
            logger.info('No Persons data to load into Elasticsearch')

    def extract(self) -> None:
        logger.info('Start extract Persons data from PostgreSQL')
        return Person.objects.select_modified(modified=self.last_modified)

    def transform(self, data) -> None:
        """
        Трансформирует извлеченные экземпляры персонажей для Elasticsearch.
        """
        if data is not None:
            transformed_data: list = []
            person_ids: set = {person.get('p_id') for person in data}
            for person_id in person_ids:
                roles: Optional[list[str]] = []
                films: Optional[list[str]] = []
                actor_film_ids: Optional[list[str]] = []
                director_film_ids: Optional[list[str]] = []
                writer_film_ids: Optional[list[str]] = []
                for person in data:
                    if person.get('p_id') == person_id:
                        full_name = person.get('full_name')
                        film = person.get('film')
                        if person.get('role') not in roles:
                            roles.append(person.get('role'))
                        if person.get('film') not in films:
                            films.append(person.get('film'))
                        if person.get('role') == 'actor':
                            if film not in actor_film_ids:
                                actor_film_ids.append(film)
                        elif person.get('role') == 'director':
                            if film not in director_film_ids:
                                director_film_ids.append(film)
                        elif person.get('role') == 'writer':
                            if film not in writer_film_ids:
                                writer_film_ids.append(film)
                        new_person = {
                            'id': person_id,
                            'full_name': full_name,
                            'roles': roles,
                            'film_ids': films,
                            'actor_film_ids': actor_film_ids,
                            'director_film_ids': director_film_ids,
                            'writer_film_ids': writer_film_ids,
                        }
                transformed_data.append(new_person)
            return transformed_data
