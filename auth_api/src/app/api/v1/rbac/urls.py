from flask import Blueprint

from .views import RolesAPI, RolesUsersAPI, UsersAPI, UsersRolesAPI

router = Blueprint('rbac', __name__, url_prefix='/rbac')

roles_view = RolesAPI.as_view('role_api')

router.add_url_rule('/users/',
                    view_func=UsersAPI.as_view('users'),
                    methods=['GET'])

router.add_url_rule('/roles/',
                    defaults={'role_id': None},
                    view_func=roles_view,
                    endpoint='without_role_id',
                    methods=['GET'])
router.add_url_rule('/roles/',
                    view_func=roles_view,
                    methods=['POST'])
router.add_url_rule('/roles/<uuid:role_id>',
                    view_func=roles_view,
                    endpoint='with_role_id',
                    methods=['GET', 'PATCH', 'DELETE'])

router.add_url_rule('/roles/<uuid:role_id>/users/',
                    view_func=RolesUsersAPI.as_view('roles_users'),
                    methods=['GET', 'POST', 'DELETE'])

router.add_url_rule('/users/<uuid:user_id>/roles/',
                    view_func=UsersRolesAPI.as_view('users_roles'),
                    methods=['GET', 'POST', 'DELETE'])
