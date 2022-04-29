from flask import jsonify
from flask_babel import _
from werkzeug.http import HTTP_STATUS_CODES

from . import core


def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, _('Unknown error'))}
    if message is not None:
        payload['msg'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


@core.app_errorhandler(400)
def bad_request(error):
    return error_response(error.code, error.description)


@core.app_errorhandler(404)
def not_found_error(error):
    return error_response(error.code, error.description)


@core.app_errorhandler(405)
def method_not_allowed(error):
    return error_response(error.code, error.description)


@core.app_errorhandler(429)
def ratelimit_handler(error):
    return error_response(error.code, error.description)


@core.app_errorhandler(500)
def internal_error(error):
    return error_response(error.code, error.description)
