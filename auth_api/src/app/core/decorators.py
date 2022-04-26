from functools import wraps
from http import HTTPStatus

from flask import jsonify
from flask_babel import _
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def superuser_required(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get('is_superuser', None):
            return fn(*args, **kwargs)
        else:
            return jsonify(msg=_('Superuser only!')), HTTPStatus.FORBIDDEN

    return decorator


def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('is_superuser', None):
                return fn(*args, **kwargs)
            if set(claims.get('roles', None)) == set(roles):
                return fn(*args, **kwargs)
            else:
                return jsonify(msg=_('Insufficient permissions')), HTTPStatus.FORBIDDEN

        return decorator
    return wrapper


def roles_accepted(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('is_superuser', None):
                return fn(*args, **kwargs)
            for role in claims.get('roles'):
                if role in roles:
                    return fn(*args, **kwargs)
            return jsonify(msg=_('Insufficient permissions')), HTTPStatus.FORBIDDEN
        return decorator
    return wrapper
