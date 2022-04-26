from flask import Blueprint

from .v1.urls import v1

api = Blueprint('api', __name__, url_prefix='/api')

api.register_blueprint(v1)
