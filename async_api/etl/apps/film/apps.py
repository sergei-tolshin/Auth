import logging
from typing import Optional

from services.apps import BaseApps

from .models import Film
from .schema import SCHEMA as film_schema

logger = logging.getLogger(__name__)


class FilmApps(BaseApps):
    index = 'movies'
    schema = film_schema

    def __init__(self, state, es_client, *args, **kwargs):
        super().__init__(state, es_client, *args, **kwargs)
        self.relations = self._get_relations()

    def _get_relations(self):
        return Film.objects.relations

    def run(self):
        if films := self.extract():
            logger.info('Extracted %d modified Films', len(films))
            self.states['modified'] = f'{films[-1].modified}'
            ids = [film.id for film in films]
            instanses = Film.objects.instances(ids)
            transformed_data = self.transform(instanses)

            """Если есть связанные объекты, то обновляем их"""
            if self.relations:
                for relation in self.relations:
                    self._update_relation(relation, 'film', ids)

            logger.info('Start Films data transfer to Elasticsearch')
            inserter = self.load(index=self.index, schema=self.schema)
            for _ in transformed_data:
                inserter.send(_)
            inserter.close()

            logger.info('Save Films state of data modified')
            self.save_state()
        else:
            logger.info('No Films data to load into Elasticsearch')

    def extract(self) -> None:
        logger.info('Start extract Films data from PostgreSQL')
        return Film.objects.select_modified(modified=self.last_modified)

    def transform(self, data) -> None:
        """
        Трансформирует извлеченные экземпляры фильмов для Elasticsearch.
        Формирует список уникальных фильмов с группировкой списков и
        экземпляров genre, director, actor, writer
        """
        if data is not None:
            transformed_data: list = []
            film_ids: set = {film.get('fw_id') for film in data}
            for film_id in film_ids:
                genres: Optional[list[dict[str, str]]] = []
                directors_names: Optional[list[str]] = []
                actors_names: Optional[list[str]] = []
                writers_names: Optional[list[str]] = []
                directors: Optional[list[dict[str, str]]] = []
                actors: Optional[list[dict[str, str]]] = []
                writers: Optional[list[dict[str, str]]] = []
                for film in data:
                    if film.get('fw_id') == film_id:
                        imdb_rating = film.get('rating')
                        title = film.get('title')
                        description = film.get('description')
                        film_type = film.get('type')
                        genre_name = film.get('genre')
                        genre_instance = {'id': film.get('genre_id'),
                                          'name': genre_name}
                        if genre_instance not in genres:
                            genres.append(genre_instance)
                        person_name = film.get('full_name')
                        person_instance = {'id': film.get('person_id'),
                                           'name': person_name}
                        if film.get('role') == 'director':
                            if person_name not in directors_names:
                                directors_names.append(person_name)
                            if person_instance not in directors:
                                directors.append(person_instance)
                        elif film.get('role') == 'actor':
                            if person_name not in actors_names:
                                actors_names.append(person_name)
                            if person_instance not in actors:
                                actors.append(person_instance)
                        elif film.get('role') == 'writer':
                            if person_name not in writers_names:
                                writers_names.append(person_name)
                            if person_instance not in writers:
                                writers.append(person_instance)
                        new_film = {
                            'id': film_id,
                            'imdb_rating': imdb_rating,
                            'title': title,
                            'description': description,
                            'film_type': film_type,
                            'genre': genres,
                            'directors_names': directors_names,
                            'actors_names': actors_names,
                            'writers_names': writers_names,
                            'directors': directors,
                            'actors': actors,
                            'writers': writers,
                        }
                transformed_data.append(new_film)
            return transformed_data
