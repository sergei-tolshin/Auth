from http import HTTPStatus

import pyotp
from app import limiter
from app.core.errors import error_response
from app.db.cache import delete_token, revoke_token
from app.models.journal import Action, Journal
from app.models.user import User
from app.schemas.user import CodeSchema, LoginSchema
from flasgger import SwaggerView, swag_from
from flask import abort, jsonify, redirect, request, url_for
from flask_babel import _
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError


class LoginAPI(SwaggerView):
    decorators = [limiter.limit('5/minute')]

    @swag_from('docs/login_post.yml')
    def post(self):
        """Вход пользователя в аккаунт"""
        schema = LoginSchema()
        data = request.get_json()

        try:
            data = schema.load(data)
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        user = User.find_by_email(data.get('email'))
        if user is None or not user.check_password(data.get('password')):
            abort(HTTPStatus.NOT_FOUND,
                  description=_('Invalid email or password'))

        if user.totp and user.totp.confirmed:
            return redirect(url_for('.check', user_id=user.id))

        event = Journal(Action.login, request)
        user.events.append(event)
        user.save()

        token_pair = user.encode_token_pair()
        return jsonify(token_pair), HTTPStatus.OK


class LogoutAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/logout_delete.yml')
    def delete(self):
        """Выход пользователя из аккаунта"""
        identity = get_jwt_identity()
        user = User.find_by_id(identity)
        event = Journal(Action.logout, request)
        user.events.append(event)
        user.save()
        revoke_token(get_jwt())
        return jsonify(msg=_('Access token revoked, session closed')), \
            HTTPStatus.OK


class TokenRefreshAPI(SwaggerView):
    decorators = [limiter.limit('5/minute')]

    @jwt_required(refresh=True, locations='json')
    @swag_from('docs/token_refresh_post.yml')
    def post(self):
        """Выдача новой пары токенов в обмен на корректный refresh токен"""
        delete_token(get_jwt())

        identity = get_jwt_identity()
        user = User.find_by_id(identity)
        token_pair = user.encode_token_pair()

        return jsonify(token_pair), HTTPStatus.OK


class TokenVerifyAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/token_verify_post.yml')
    def post(self):
        """Проверка валидности токена"""
        identity = get_jwt_identity()
        user = User.find_by_id(identity)
        if not user or not user.is_active:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  _('Token failed verification'))
        return jsonify(msg=_('The token has been verified')), HTTPStatus.OK


class CheckAPI(SwaggerView):
    @swag_from('docs/check_get.yml')
    def get(self, user_id):
        """Перенаправление для двухфакторной аутентификации"""
        return jsonify({'id': user_id}), HTTPStatus.OK

    @swag_from('docs/check_post.yml')
    def post(self, user_id):
        """Ввод кода двухфакторной аутентификации"""
        schema = CodeSchema()
        data = request.get_json()

        try:
            data = schema.load(data)
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        user = User.query.get_or_404(user_id, _('User not found'))
        totp = pyotp.TOTP(user.totp.key)

        if not totp.verify(data.get('code')):
            abort(HTTPStatus.NOT_FOUND, description=_('Invalid code'))

        event = Journal(Action.login, request)
        user.events.append(event)
        user.save()

        token_pair = user.encode_token_pair()
        return jsonify(token_pair), HTTPStatus.OK
