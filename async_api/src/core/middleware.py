import logging
from http import HTTPStatus
from typing import List, Tuple

import grpc
from aiobreaker import CircuitBreaker
from fastapi import FastAPI
from fastapi.requests import HTTPConnection
from fastapi.responses import JSONResponse
from jose import ExpiredSignatureError, JWTError, jwt
from starlette.authentication import (AuthCredentials, AuthenticationBackend,
                                      BaseUser, UnauthenticatedUser)
from starlette.types import Receive, Scope, Send

from core.auth.user_pb2 import UserInfoRequest
from core.auth.user_pb2_grpc import UserStub

from .errors import (AuthConnectorError, AuthenticationHeaderMissing,
                     UserNotActive, UserNotFound)

auth_breaker = CircuitBreaker(fail_max=5)


class FastAPIUser(BaseUser):
    def __init__(self, first_name: str, last_name: str, age: int,
                 email: str, user_id: any):
        self.user_id = user_id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.age = age

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
        auth_channel: str = None,
    ):
        self.app = app
        self.backend: AuthBackend = AuthBackend(
            secret_key=secret_key,
            get_scopes=get_scopes,
            get_user=get_user,
            algorithms=algorithms,
            auth_channel=auth_channel,
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
        except ExpiredSignatureError:
            response = self.token_has_expired()
            await response(scope, receive, send)
            return
        except (
            AuthConnectorError,
            AuthenticationHeaderMissing,
            JWTError,
            UserNotActive,
            UserNotFound
        ):
            scope['auth'], scope['user'] = AuthCredentials(scopes=[]), \
                UnauthenticatedUser()
            await self.app(scope, receive, send)

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
        auth_channel
    ):
        self.secret_key = secret_key
        self.algorithms = algorithms
        self.auth_channel = auth_channel

        if get_scopes is None:
            self.get_scopes = self._get_scopes
        else:
            self.get_scopes = get_scopes

        if get_user is None:
            self.get_user = self._get_user
        else:
            self.get_user = get_user

    @staticmethod
    def _get_scopes(roles: str) -> List[str]:
        try:
            roles = roles.split(',')
            return roles
        except KeyError or AttributeError:
            return []

    @staticmethod
    def _get_user(user) -> FastAPIUser:
        try:
            name_segments = user.name.split(' ')
            first_name, last_name = name_segments[0], name_segments[-1]
        except AttributeError:
            first_name, last_name = None, None

        return FastAPIUser(user_id=user.id,
                           email=user.email,
                           first_name=first_name,
                           last_name=last_name,
                           age=user.age)

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

        try:
            user_id = decoded_token.get('sub')
            user_info = await self.get_user_info_request(user_id)
        except grpc.RpcError as error:
            if error.code() == grpc.StatusCode.NOT_FOUND:
                raise UserNotFound
            if error.code() == grpc.StatusCode.UNAUTHENTICATED:
                raise UserNotActive
            if error.code() == grpc.StatusCode.UNAVAILABLE:
                logging.warning('Auth service is unavailable')
                raise AuthConnectorError

        scopes = self.get_scopes(user_info.roles)
        user = self.get_user(user_info)

        return AuthCredentials(scopes=scopes), user

    @auth_breaker
    async def get_user_info_request(self, id):
        stub = UserStub(self.auth_channel)
        response = await stub.GetInfo(UserInfoRequest(id=id))
        logging.info(response)
        return response
