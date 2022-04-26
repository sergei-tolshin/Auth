from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv()


class PostgresSettings(BaseSettings):
    """Параметры настроек для PostgreSQL"""
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: Optional[str] = 'localhost'
    DB_PORT: Optional[int] = 5432
    DB_OPTIONS: str

    class Config:
        env_file = '.env'


class ElasticsearchSettings(BaseSettings):
    """Параметры настроек для Elasticsearch"""
    ES_HOST: str = 'localhost'
    ES_PORT: Optional[int] = 9200
    ES_SETTINGS: dict = {
        'refresh_interval': '1s',
        'analysis': {
            'filter': {
                'english_stop': {
                    'type': 'stop',
                    'stopwords': '_english_'
                },
                'english_stemmer': {
                    'type': 'stemmer',
                    'language': 'english'
                },
                'english_possessive_stemmer': {
                    'type': 'stemmer',
                    'language': 'possessive_english'
                },
                'russian_stop': {
                    'type': 'stop',
                    'stopwords': '_russian_'
                },
                'russian_stemmer': {
                    'type': 'stemmer',
                    'language': 'russian'
                }
            },
            'analyzer': {
                'ru_en': {
                    'tokenizer': 'standard',
                    'filter': [
                        'lowercase',
                        'english_stop',
                        'english_stemmer',
                        'english_possessive_stemmer',
                        'russian_stop',
                        'russian_stemmer'
                    ]
                }
            }
        }
    }

    class Config:
        env_file = '.env'


class ETLSettings(BaseSettings):
    """Параметры настроек для ETL"""
    LIMIT: Optional[int] = 100
    UPLOAD_INTERVAL: float
    STATE_FIELD: str
    STATE_FILE_NAME: str
    INSTALLED_APPS: List[str] = [
        'film',
        'genre',
        'person',
    ]

    class Config:
        env_file = '.env'


pg_settings = PostgresSettings()
es_settings = ElasticsearchSettings()
etl_settings = ETLSettings()
