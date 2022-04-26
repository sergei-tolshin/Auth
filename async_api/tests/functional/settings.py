import os

import orjson
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Настройки FastAPI
    SERVICE_HOST: str = os.getenv('SERVICE_HOST', '127.0.0.1')
    SERVICE_PORT: int = int(os.getenv('SERVICE_PORT', 8000))
    SERVICE_URL: str = f'http://{SERVICE_HOST}:{SERVICE_PORT}'

    # Настройки Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', '127.0.0.1')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', 6379))

    # Настройки Elasticsearch
    ELASTIC_HOST: str = os.getenv('ELASTIC_HOST', '127.0.0.1')
    ELASTIC_PORT: int = int(os.getenv('ELASTIC_PORT', 9200))
    ELASTIC_URL: str = f'{ELASTIC_HOST}:{ELASTIC_PORT}'
    ELASTIC_INDEX = orjson.loads(os.getenv(
        'ELASTIC_INDEX',
        '{"films": "test_movies", "genres": "test_genres", "persons": "test_persons"}'
    ))
    ELASTIC_SETTINGS: dict = {
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


config = Settings()
