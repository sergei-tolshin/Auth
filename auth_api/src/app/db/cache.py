from datetime import datetime
from http import HTTPStatus

import orjson
from app import cache
from flask import abort, current_app, request
from flask_babel import _
from flask_jwt_extended import decode_token

import redis


def set_token(token):
    payload = decode_token(token)
    user = payload['sub']
    jti = payload['jti']
    session_info = {
        'ip': request.environ.get('HTTP_X_FORWARDED_FOR',
                                  request.remote_addr),
        'user_agent': request.user_agent.string,
        'last_activity': datetime.now().isoformat()
    }
    cache.setex(
        f'user:{user}:{jti}',
        current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
        orjson.dumps(session_info)
    )
    return True


def delete_token(token):
    user = token['sub']
    jti = token['jti']
    cache.delete(f'user:{user}:{jti}')


def revoke_token(access_token):
    exp_access_token = access_token['exp']
    jti_access_token = access_token['jti']
    jti_refresh_token = access_token['rti']
    identity = access_token['sub']

    remaining_time = exp_access_token - datetime.now().timestamp()

    def revoke_pair_token(pipeline: redis.client.Pipeline) -> None:
        pipeline.setex(f'blocklist:{jti_access_token}', int(remaining_time), 0)
        pipeline.delete(f'user:{identity}:{jti_refresh_token}')

    cache.transaction(revoke_pair_token)

    return cache.keys()


def get_session(identity, session_id=None):
    if session_id is not None:
        key = f'user:{identity}:{session_id}'
        value = cache.get(key) or None
        if not value:
            abort(HTTPStatus.NOT_FOUND, description=_('Session not found'))
        data = orjson.loads(value.decode())
        data['id'] = session_id
    else:
        data = []
        for key in cache.scan_iter(f'user:{identity}:*'):
            id = {'id': key.decode().split(':')[2]}
            value = orjson.loads(cache.get(key).decode())
            data.append(id | value)
    return data


def delete_session(token, session_id=None):
    user = token['sub']
    rti = token['rti']

    if session_id is not None:
        key = f'user:{user}:{session_id}'
        cache.delete(key)
    else:
        current_session = f'user:{user}:{rti}'
        keys = f'user:{user}:*'

        pipeline = cache.pipeline()
        cursor, keys = cache.scan(match=keys, count=1000)
        keys.remove(current_session.encode())
        if keys:
            cache.delete(*keys)
        pipeline.execute()
