from http import HTTPStatus

from app import limiter
from app.core.errors import error_response
from app.db.cache import delete_session, get_session
from app.models.journal import Action, Journal
from app.models.user import TOTPDevice, User
from app.schemas.journal import JournalSchema, SessionSchema
from app.schemas.user import (ChangeEmailSchema, ChangePasswordSchema,
                              CodeSchema, ProfileSchema, RegisterSchema,
                              UserSchema)
from flasgger import SwaggerView, swag_from
from flask import abort, jsonify, request
from flask_babel import _
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from marshmallow import ValidationError


class RegisterAPI(SwaggerView):
    decorators = [limiter.limit('5/minute')]

    @swag_from('docs/register.yml')
    def post(self):
        """Регистрация пользователя"""
        schema = RegisterSchema()
        data = request.get_json()

        try:
            data = schema.load(data)
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        user = User(**data)
        user = user.save()

        return jsonify(id=user.id), HTTPStatus.CREATED


class AccountAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/profile_get.yml')
    def get(self):
        """Аккаунт пользователя"""
        schema = UserSchema()
        identity = get_jwt_identity()
        user = User.query.get_or_404(identity, _('User not found'))
        return jsonify(schema.dump(user)), HTTPStatus.OK

    @jwt_required()
    @swag_from('docs/profile_patch.yml')
    def patch(self):
        """Изменение профиля"""
        schema = ProfileSchema()

        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        identity = get_jwt_identity()
        user = User.query.get_or_404(identity, _('User not found'))
        user.profile.update(data)
        user.save()

        return jsonify(msg=_('Profile updated')), HTTPStatus.OK


class ChangeEmailAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/change_email_post.yml')
    def post(self):
        """Изменение адреса электронной почты"""
        schema = ChangeEmailSchema()

        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        identity = get_jwt_identity()
        user = User.query.get_or_404(identity, _('User not found'))

        if user.email != data.get('current_email'):
            abort(HTTPStatus.NOT_FOUND, description=_('Invalid current email'))

        user.email = data.get('new_email')
        event = Journal(Action.change_email, request)
        user.events.append(event)
        user.save()

        if data.get('logout_everywhere'):
            delete_session(get_jwt())

        return jsonify(msg=_('Email changed successfully')), HTTPStatus.OK


class ChangePasswordAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/change_password_post.yml')
    def post(self):
        """Изменение пароля"""
        schema = ChangePasswordSchema()

        try:
            data = schema.load(request.get_json())
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        identity = get_jwt_identity()
        user = User.query.get_or_404(identity, _('User not found'))

        if not user.check_password(data.get('current_password')):
            abort(HTTPStatus.NOT_FOUND,
                  description=_('Invalid current password'))

        user.set_password(data.get('new_password'))
        event = Journal(Action.change_password, request)
        user.events.append(event)
        user.save()

        if data.get('logout_everywhere'):
            delete_session(get_jwt())

        return jsonify(msg=_('Password changed successfully')), HTTPStatus.OK


class JournalAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/journal_get.yml')
    def get(self):
        """История событий (действия пользователя)"""
        schema = JournalSchema(many=True)
        identity = get_jwt_identity()
        events = Journal.get_by_user(identity)
        return jsonify(schema.dump(events))


class SessionsAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/sessions_no_id_get.yml',
               endpoint='api.v1.account.without_id')
    @swag_from('docs/sessions_with_id_get.yml',
               endpoint='api.v1.account.with_id')
    def get(self, session_id):
        """Информация о сеансе/сеансах"""
        schema = SessionSchema()
        identity = get_jwt_identity()
        if session_id is None:
            result = get_session(identity)
            return jsonify(schema.load(result, many=True)), HTTPStatus.OK
        else:
            result = get_session(identity, session_id)
            return jsonify(schema.load(result)), HTTPStatus.OK

    @jwt_required()
    @swag_from('docs/sessions_no_id_delete.yml',
               endpoint='api.v1.account.without_id')
    @swag_from('docs/sessions_with_id_delete.yml',
               endpoint='api.v1.account.with_id')
    def delete(self, session_id):
        """Завершить сеанс/сеансы"""
        if session_id is None:
            delete_session(get_jwt())
            return jsonify(msg=_('All sessions are closed')), HTTPStatus.OK
        else:
            delete_session(get_jwt(), session_id)
            return jsonify(msg=_('Session %(id)s is closed',
                                 id=session_id)), HTTPStatus.NO_CONTENT


class TOTPDeviceAPI(SwaggerView):
    @jwt_required()
    @swag_from('docs/totp_get.yml')
    def get(self):
        """Включение двухфакторной аутентификации"""
        identity = get_jwt_identity()
        user = User.query.get_or_404(identity, _('User not found'))

        if user.totp and user.totp.confirmed:
            return error_response(
                HTTPStatus.FORBIDDEN,
                _('Two-factor authentication is already enabled'))
        user.totp = TOTPDevice()
        provisioning_url = user.totp.enabled()

        return jsonify(url=provisioning_url), HTTPStatus.OK

    @jwt_required()
    @swag_from('docs/totp_post.yml')
    def post(self):
        """Подтверждение включения двухфакторной аутентификации"""
        schema = CodeSchema()
        data = request.get_json()

        try:
            data = schema.load(data)
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        identity = get_jwt_identity()
        user = User.query.get_or_404(identity, _('User not found'))
        if user.totp and user.totp.confirmed:
            return error_response(
                HTTPStatus.FORBIDDEN,
                _('Two-factor authentication is already enabled'))

        if not user.totp.verify(data.get('code')):
            return error_response(HTTPStatus.UNAUTHORIZED, _('Invalid code'))

        user.totp.confirmed = True
        user.save()

        return jsonify(msg=_('Two-factor authentication is enabled')), \
            HTTPStatus.CREATED

    @jwt_required()
    @swag_from('docs/totp_delete.yml')
    def delete(self):
        """Отключение двухфакторной аутентификации"""
        schema = CodeSchema()
        data = request.get_json()

        try:
            data = schema.load(data)
        except ValidationError as err:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  err.messages)

        identity = get_jwt_identity()
        user = User.query.get_or_404(identity, _('User not found'))

        if not user.totp:
            return error_response(
                HTTPStatus.FORBIDDEN,
                _('Two-factor authentication is already disabled'))

        if not user.totp.verify(data.get('code')):
            return error_response(HTTPStatus.UNAUTHORIZED, _('Invalid code'))

        user.totp.delete()
        return jsonify(msg=_('Two-factor authentication is disabled')), \
            HTTPStatus.NO_CONTENT
