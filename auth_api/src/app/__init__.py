from flasgger import Swagger
from flask import Flask
from flask_babel import Babel
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy

from app.core.config import DevelopmentConfig
from app.core.middleware import RateLimiter
from app.core.tracer import Tracer
from app.db.redis import Redis

limiter = Limiter(key_func=get_remote_address)
rate_limiter = RateLimiter(limit='10/second')
tracer = Tracer(console=False)
db = SQLAlchemy()
migrate = Migrate()
cache = Redis()
ma = Marshmallow()
jwt = JWTManager()
security = Security()
swagger = Swagger()
babel = Babel()


def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    tracer.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    swagger.init_app(app)
    babel.init_app(app)

    from app.core.datastore import user_datastore
    security.init_app(app, user_datastore)

    from app.core.cli import create
    from app.core import core, jwt_callback
    from app.api.urls import api

    app.register_blueprint(create)
    app.register_blueprint(core)
    app.register_blueprint(api)

    """
    Для ограничения количества запросов к серверу (Rate limit) подключено
    расширение Flask-Limiter, но для задания спринта реализован алгоритм
    Token bucket с использованием Redis
    """
    # limiter.init_app(app)
    rate_limiter.init_app(app)

    return app
