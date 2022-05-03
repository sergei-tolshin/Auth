from http import HTTPStatus

from app import cache, jwt
from app.core.errors import error_response


@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id


@jwt.additional_claims_loader
def additional_claims_lookup(user):
    roles = [role.name for role in user.roles] or []
    if user.is_superuser:
        roles.append('superuser')

    claims = {
        'roles': ','.join(roles)
    }
    return claims


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(header, payload):
    jti = payload['jti']
    token_in_cache = cache.get(f'blocklist:{jti}')
    return token_in_cache is not None


@jwt.token_verification_loader
def check_if_token_is_verification(header, payload):
    user = payload['sub']
    jti = payload['rti'] if payload['type'] == 'access' else payload['jti']
    token_in_cache = cache.get(f'user:{user}:{jti}')
    return token_in_cache is not None


@jwt.token_verification_failed_loader
def invalid_token_callback(header, payload):
    return error_response(HTTPStatus.FORBIDDEN, 'Token verification failed')
