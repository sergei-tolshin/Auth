import logging
from importlib import import_module
from time import sleep

from config.settings import es_settings, pg_settings
from db.elastic import ElasticsearchDatabase
from db.manager import BaseManager
from db.postgres import PostgresDatabase
from utils.state import JsonFileStorage, State

logger = logging.getLogger(__name__)


class ETL:
    def __init__(self, conf=None):
        self.conf = conf
        self.state = None
        self.pg_client = None
        self.es_client = None
        self.states = None
        self.registered_apps = self.__register_apps()

    def __enter__(self):
        self.state = self.__get_state()
        if self.state.get_state('etl_process') == 'started':
            error = 'ETL process already started, please stop it before run!'
            logger.warning(error)
            raise RuntimeWarning(error)

        try:
            self.pg_client = PostgresDatabase(settings=pg_settings).connection
            self.es_client = ElasticsearchDatabase(settings=es_settings)
            BaseManager.set_connection(conn=self.pg_client)
            BaseManager.set_limit(limit=self.conf.LIMIT)
        except Exception:
            self.state.set_state('etl_process', 'stopped')
            raise
        else:
            logger.info('ETL process started')
            self.state.set_state('etl_process', 'started')
            return self

    def __exit__(self, type, value, traceback):
        logger.info('Close all connections ...')
        if self.es_client is not None:
            self.es_client.close()

        if self.pg_client and not self.pg_client.closed:
            self.pg_client.close()
            logger.info('PostgreSQL connection closed')

        logger.info('ETL process stopped')
        self.state.set_state('etl_process', 'stopped')

        logger.info('Pause %s seconds', self.conf.UPLOAD_INTERVAL)
        sleep(self.conf.UPLOAD_INTERVAL)

    def __get_state(self):
        """Хранилище состояний"""
        storage = JsonFileStorage(file_name=self.conf.STATE_FILE_NAME)
        return State(storage=storage)

    def __register_apps(self):
        """Регистрирует приложения"""
        registered_apps = list()
        for installed_app in self.conf.INSTALLED_APPS:
            app_path = '%s.%s' % (f'apps.{installed_app}', 'apps')
            try:
                app_import = import_module(app_path)
                app_class = getattr(
                    app_import, f'{installed_app.title()}Apps')
            except ModuleNotFoundError as error:
                logger.error(error)
                raise
            except AttributeError as error:
                logger.error(error)
                raise
            else:
                registered_apps.append(app_class)
        return registered_apps
