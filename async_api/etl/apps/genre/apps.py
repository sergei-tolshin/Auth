import logging
from services.apps import BaseApps

from .models import Genre
from .schema import SCHEMA as genre_schema

logger = logging.getLogger(__name__)


class GenreApps(BaseApps):
    index = 'genres'
    schema = genre_schema

    def __init__(self, state, es_client, *args, **kwargs):
        super().__init__(state, es_client, *args, **kwargs)
        self.relations = self._get_relations()

    def _get_relations(self):
        return Genre.objects.relations

    def run(self):
        if genres := self.extract():
            logger.info('Extracted %d modified Genres', len(genres))
            self.states['modified'] = f'{genres[-1].modified}'
            ids = [genre.id for genre in genres]
            instanses = Genre.objects.instances(ids)
            transformed_data = self.transform(instanses)

            """Если есть связанные объекты, то обновляем их"""
            if self.relations:
                for relation in self.relations:
                    self._update_relation(relation, 'genre', ids)

            logger.info('Start Genres data transfer to Elasticsearch')
            inserter = self.load(index=self.index, schema=self.schema)
            for _ in transformed_data:
                inserter.send(_)
            inserter.close()

            logger.info('Save Genres state of data modified')
            self.save_state()
        else:
            logger.info('No Genres data to load into Elasticsearch')

    def extract(self) -> None:
        logger.info('Start extract Genres data from PostgreSQL')
        return Genre.objects.select_modified(modified=self.last_modified)

    def transform(self, data) -> None:
        """
        Трансформирует извлеченные экземпляры жанров для Elasticsearch
        """
        transformed_data: list = []
        for genre in data:
            new_genre = {
                'id': genre.get('id'),
                'name': genre.get('name'),
                'description': genre.get('description'),
            }
            transformed_data.append(new_genre)
        return transformed_data
