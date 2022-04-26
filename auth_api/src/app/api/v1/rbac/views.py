from http import HTTPStatus

from app.core.decorators import roles_accepted
from app.core.errors import error_response
from app.models.rbac import Role
from app.models.user import User
from app.schemas.rbac import RoleSchema, UserSchema
from flasgger import SwaggerView, swag_from
from flask import jsonify, request
from flask_babel import _
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError


class UsersAPI(SwaggerView):
    decorators = [jwt_required(), roles_accepted('admin')]

    @swag_from('docs/users_get.yml')
    def get(self):
        """Список пользователей"""
        schema = UserSchema(many=True)
        users = User.all()
        return jsonify(schema.dump(users)), HTTPStatus.OK


class RolesAPI(SwaggerView):
    decorators = [jwt_required(), roles_accepted('admin')]

    @swag_from('docs/roles_no_role_id_get.yml',
               endpoint='api.v1.rbac.without_role_id')
    @swag_from('docs/roles_with_role_id_get.yml',
               endpoint='api.v1.rbac.with_role_id')
    def get(self, role_id):
        """Информация о ролях/роли"""
        if role_id is None:
            schema = RoleSchema(only=('id', 'name'), many=True)
            roles = Role.all()
            return jsonify(schema.dump(roles)), HTTPStatus.OK
        else:
            schema = RoleSchema()
            role = Role.query.get_or_404(role_id, _('Role not found'))
            return jsonify(schema.dump(role)), HTTPStatus.OK

    @swag_from('docs/roles_post.yml')
    def post(self):
        """Создать роль"""
        schema = RoleSchema(only=('name', 'description'))

        try:
            data = schema.load(request.get_json())
        except ValidationError as error:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  error.messages)

        role = Role(**data)
        role.save()

        return jsonify(msg=_('Role created')), HTTPStatus.CREATED

    @swag_from('docs/roles_patch.yml')
    def patch(self, role_id):
        """Изменить роль"""
        schema = RoleSchema(only=('name', 'description'))

        try:
            data = schema.load(request.get_json())
        except ValidationError as error:
            return error_response(HTTPStatus.UNPROCESSABLE_ENTITY,
                                  error.messages)

        role = Role.query.get_or_404(role_id, _('Role not found'))
        role.update(data)
        role.save()

        return jsonify(msg=_('Role changed')), HTTPStatus.OK

    @swag_from('docs/roles_delete.yml')
    def delete(self, role_id):
        """Удалить роль"""
        role = Role.query.get_or_404(role_id, _('Role not found'))
        role.delete()
        return jsonify(msg=_('Role deleted')), HTTPStatus.NO_CONTENT


class RolesUsersAPI(SwaggerView):
    decorators = [jwt_required(), roles_accepted('admin')]
    tags = ['rbac']

    @swag_from('docs/roles_users_get.yml')
    def get(self, role_id):
        """Пользователи с ролью"""
        schema = UserSchema(many=True)
        role = Role.query.get_or_404(role_id, _('Role not found'))

        return jsonify(schema.dump(role.users)), HTTPStatus.OK

    @swag_from('docs/roles_users_post.yml')
    def post(self, role_id):
        """Добавить пользователям роль"""
        role = Role.query.get_or_404(role_id, _('Role not found'))
        user_ids = request.get_json()['users']

        users = User.query.filter(User.id.in_(user_ids)).all()
        role.add_to_users(users)

        return jsonify(msg=_('Role "%(name)s" added to users',
                             name=role.name)), HTTPStatus.OK

    @swag_from('docs/roles_users_delete.yml')
    def delete(self, role_id):
        """Отобрать у пользователей роль"""
        role = Role.query.get_or_404(role_id, _('Role not found'))
        user_ids = request.get_json()['users']

        users = User.query.filter(User.id.in_(user_ids)).all()
        role.remove_from_users(users)

        return jsonify(msg=_('Role "%(name)s" removed from users',
                             name=role.name)), HTTPStatus.OK


class UsersRolesAPI(SwaggerView):
    decorators = [jwt_required(), roles_accepted('admin')]
    tags = ['rbac']

    @swag_from('docs/users_roles_get.yml')
    def get(self, user_id):
        """Роли пользователя"""
        schema = RoleSchema(only=('id', 'name'), many=True)
        user = User.query.get_or_404(user_id, _('User not found'))

        return jsonify(schema.dump(user.roles)), HTTPStatus.OK

    @swag_from('docs/users_roles_post.yml')
    def post(self, user_id):
        """Добавить пользователю роль"""
        user = User.query.get_or_404(user_id, _('User not found'))
        roles = request.get_json()['roles']

        user.add_roles(roles)

        return jsonify(msg=_('Role added to user')), HTTPStatus.OK

    @swag_from('docs/users_roles_delete.yml')
    def delete(self, user_id):
        """Отобрать у пользователя роль"""
        user = User.query.get_or_404(user_id, _('User not found'))
        roles = request.get_json()['roles']

        user.remove_roles(roles)

        return jsonify(msg=_('Roles removed from user')), HTTPStatus.OK
