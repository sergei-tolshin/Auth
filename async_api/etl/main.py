import logging
import logging.config

from config.settings import etl_settings as conf
from services.etl import ETL

"""Настройка логирования"""
_log_format = ("%(asctime)s - [%(levelname)s] - %(name)s "
               "(%(filename)s).%(funcName)s(%(lineno)d) > %(message)s")
logging.basicConfig(filename='logs.log',
                    level=logging.INFO,
                    format=_log_format,
                    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)


def main():
    while True:
        with ETL(conf=conf) as etl:

            for registered_app in etl.registered_apps:
                app = registered_app(state=etl.state, es_client=etl.es_client)
                app.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info('ETL process interrupted')
