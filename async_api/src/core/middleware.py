import logging
from http import HTTPStatus
from typing import List, Tuple

import aiohttp
from aiobreaker import CircuitBreaker
from fastapi import FastAPI
from fastapi.requests import HTTPConnection
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, jwt
from starlette.authentication import (AuthCredentials, AuthenticationBackend,
                                      BaseUser, UnauthenticatedUser)
from starlette.types import Receive, Scope, Send

auth_breaker = CircuitBreaker(fail_max=5)


class AuthenticationHeaderMissing(Exception):
    pass


class TokenHasExpired(Exception):
    pass


class TokenNotVerification(Exception):
    pass


class AuthConnectorError(Exception):
    pass


class FastAPIUser(BaseUser):
    def __init__(self, first_name: str, last_name: str, user_id: any):
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @property
    def identity(self) -> str:
        return self.user_id


class AuthMiddleware:
    def __init__(
        self, app: FastAPI,
        secret_key: str,
        get_scopes: callable = None,
        get_user: callable = None,
        algorithms: str or List[str] = None,
        auth_url: str = None
    ):
        self.app = app
        self.backend: AuthBackend = AuthBackend(
            secret_key=secret_key,
            get_scopes=get_scopes,
            get_user=get_user,
            algorithms=algorithms,
            auth_url=auth_url
        )

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send
    ) -> None:
        if scope['type'] not in ['http', 'websocket']:
            await self.app(scope, receive, send)
            return

        conn = HTTPConnection(scope)

        try:
            scope['auth'], scope['user'] = await self.backend.authenticate(conn)
            await self.app(scope, receive, send)
        except (
            AuthenticationHeaderMissing,
            TokenNotVerification,
            AuthConnectorError
        ):
            scope['auth'], scope['user'] = AuthCredentials(
                scopes=[]), UnauthenticatedUser()
            await self.app(scope, receive, send)
        except ExpiredSignatureError:
            response = self.token_has_expired()
            await response(scope, receive, send)
            return

    @staticmethod
    def token_has_expired(*args, **kwargs):
        return JSONResponse({'error': 'Token has expired'},
                            status_code=HTTPStatus.UNAUTHORIZED)


class AuthBackend(AuthenticationBackend):
    def __init__(
        self,
        secret_key: str,
        get_scopes: callable,
        get_user: callable,
        algorithms: str or List[str],
        auth_url
    ):
        self.secret_key = secret_key
        self.algorithms = algorithms
        self.auth_url = auth_url

        if get_scopes is None:
            self.get_scopes = self._get_scopes
        else:
            self.get_scopes = get_scopes

        if get_user is None:
            self.get_user = self._get_user
        else:
            self.get_user = get_user

    @staticmethod
    def _get_scopes(decoded_token: dict) -> List[str]:
        try:
            roles = decoded_token['roles']
            if decoded_token['is_superuser']:
                roles.append('superuser')
            return roles
        except KeyError or AttributeError:
            return []

    @staticmethod
    def _get_user(decoded_token: dict) -> FastAPIUser:
        try:
            name_segments = decoded_token.get('name').split(' ')
            first_name, last_name = name_segments[0], name_segments[-1]

        except AttributeError:
            first_name, last_name = None, None

        return FastAPIUser(user_id=decoded_token.get('sub'),
                           first_name=first_name,
                           last_name=last_name)

    async def authenticate(
        self, conn: HTTPConnection
    ) -> Tuple[AuthCredentials, BaseUser]:
        if 'Authorization' not in conn.headers:
            raise AuthenticationHeaderMissing

        auth_header = conn.headers['Authorization']
        token = auth_header.split(' ')[-1]
        decoded_token = jwt.decode(token=token,
                                   key=self.secret_key,
                                   algorithms=self.algorithms)

        scopes = self.get_scopes(decoded_token)
        user = self.get_user(decoded_token)

        try:
            token_verify = await self.send_token_verify_request(
                url=str(self.auth_url), headers=dict(conn.headers))
        except aiohttp.ClientConnectorError:
            raise AuthConnectorError

        if token_verify.status != HTTPStatus.OK:
            raise TokenNotVerification

        return AuthCredentials(scopes=scopes), user

    @auth_breaker
    async def send_token_verify_request(self, url: str, headers: dict):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers) as response:
                logging.info(response)
                return response
