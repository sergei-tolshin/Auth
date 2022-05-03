import uuid

import pytest
from app import create_app
from app.core.config import TestingConfig


@pytest.fixture(scope='session')
def app():
    app = create_app(TestingConfig)
    yield app


@pytest.fixture(scope='module')
def db(app):
    with app.app_context():
        from app import db
        db.engine.execute('CREATE SCHEMA IF NOT EXISTS auth')
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='module')
def cache(app):
    with app.app_context():
        from app import cache
        cache.flushdb()
        yield cache
        cache.flushdb()
        cache.close()


@pytest.fixture(scope='session')
def client(app):
    client = app.test_client()
    client.environ_base['HTTP_X_REQUEST_ID'] = uuid.uuid4()
    yield client


@pytest.fixture(scope='session')
def runner(app):
    return app.test_cli_runner()
