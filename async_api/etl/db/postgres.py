import logging
from typing import Optional

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
from utils.decorators import backoff

logger = logging.getLogger(__name__)


class PostgresDatabase:
    def __init__(self, settings=None):
        self.dsl: dict = {
            'dbname': settings.DB_NAME,
            'user': settings.DB_USER,
            'password': settings.DB_PASSWORD,
            'host': settings.DB_HOST,
            'port': settings.DB_PORT,
            'options': settings.DB_OPTIONS,
        }
        self.conn: Optional[_connection] = None

    @backoff(exception=OperationalError)
    def __create_conn(self) -> _connection:
        logger.info('Connecting to PostgreSQL ...')
        with psycopg2.connect(**self.dsl, cursor_factory=DictCursor) as conn:
            logger.info('Connected to PostgreSQL completed')
            return conn

    @property
    def connection(self):
        if self.conn and not self.conn.closed:
            return self.conn
        else:
            return self.__create_conn()
