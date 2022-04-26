import logging

from elasticsearch import Elasticsearch, helpers
from utils.decorators import backoff

logger = logging.getLogger(__name__)
es_log = logging.getLogger('elasticsearch')
es_log.setLevel(logging.CRITICAL)


class ElasticsearchDatabase:
    def __init__(self, settings=None):
        self.host = settings.ES_HOST
        self.port = settings.ES_PORT
        self.client = Elasticsearch([{'host': self.host, 'port': self.port}])
        self.status = True if self.__get_status_connect() else False
        self.index = None
        self.schema = None

    @backoff(exception=ConnectionError)
    def __get_status_connect(self):
        logger.info('Connecting to Elasticsearch ...')
        if not self.client.ping():
            raise ConnectionError('No connection to Elasticsearch')
        logger.info('Connected to Elasticsearch completed')
        return True

    @backoff(exception=ConnectionError)
    def get_indices(self) -> list:
        indices = list(self.client.indices.get_alias().keys())
        if self.index not in indices:
            self.create_index(self.index)
        return indices

    def close(self):
        self.client.transport.close()
        logger.info('Elasticsearch connection closed')

    def create_index(self, index: str):
        if body := self.schema:
            self.client.indices.create(index=index, body=body)
            logger.info(f"Index '{index}' created")
        else:
            logger.warning(
                "Index '%s' not created, missing schema", index)

    @backoff(exception=ConnectionError)
    def transfer_data(self, actions) -> None:
        """Добавляет пакеты данных в Elasticsearch"""
        logger.info('Get index %s ...', self.index)
        self.get_indices()
        success, failed = helpers.bulk(
            client=self.client,
            actions=[
                {'_index': self.index, '_id': action.get('id'), **action}
                for action in actions
            ],
            stats_only=True
        )
        logger.info('Transfer data to %s: success: %s, failed: %s',
                    self.index, success, failed)
