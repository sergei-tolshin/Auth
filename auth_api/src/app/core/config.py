import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret_key')

    DB_OPTIONS = '-c search_path=auth'

    SQLALCHEMY_ENGINE_OPTIONS = {'connect_args': {'options': DB_OPTIONS}}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'secret_key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)

    LANGUAGES = ['en', 'ru']
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_TRANSLATION_DIRECTORIES = 'locale'

    JSON_SORT_KEYS = False

    OAUTH_CREDENTIALS = {
        'yandex': {
            'id': os.getenv('YANDEX_CLIENT_ID'),
            'secret': os.getenv('YANDEX_CLIENT_SECRET')
        }
    }

    RATELIMIT_ENABLED = True
    RATELIMIT_STRATEGY = 'moving-window'
    RATELIMIT_DEFAULT = '1/second'
    RATELIMIT_STORAGE_URI = os.getenv(
        'RATELIMIT_STORAGE_URI',
        'redis://127.0.0.1:6379')

    TRACER_SERVICE_NAME = 'auth-api'
    TRACER_JAEGER_HOST = os.getenv('TRACER_JAEGER_HOST', '127.0.0.1')
    TRACER_JAEGER_PORT = int(os.getenv('TRACER_JAEGER_PORT', 6831))

    GRPC_PORT = int(os.getenv('GRPC_PORT', 50051))

    SWAGGER = {
        'swagger': '2.0',
        'info': {
            'title': 'Auth API',
            'description': 'Сервис аутентификации и авторизации',
            'version': '1.0.0',
        },
        'securityDefinitions': {
            'Bearer': {
                'type': 'apiKey',
                'name': 'Authorization',
                'in': 'header',
                'description': ('JWT Authorization header using'
                                'the Bearer scheme. '
                                'Example: "Authorization: Bearer {token}"')
            }
        }
    }


class DevelopmentConfig(BaseConfig):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://app:123qwe@localhost:5432/movies_database')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')


class TestingConfig(BaseConfig):
    DEBUG = True
    TESTING = True

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://app:123qwe@localhost:5432/test_database')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')


class ProductionConfig(BaseConfig):
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://app:123qwe@localhost:5432/movies_database')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
