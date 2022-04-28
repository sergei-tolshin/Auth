from flask import Blueprint, request

from .v1.urls import v1

api = Blueprint('api', __name__, url_prefix='/api')


# @api.before_app_request
# def before_request():
#     request_id = request.headers.get('X-Request-Id')
#     if not request_id:
#         raise RuntimeError('request id is required')


api.register_blueprint(v1)
