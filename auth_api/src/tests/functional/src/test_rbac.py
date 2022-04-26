import uuid
from http import HTTPStatus

import pytest
from app.models.rbac import Role, RolesUsers
from app.models.user import Journal, Profile, User
from tests.functional.testdata.factories import RoleFactory, UserFactory


@pytest.fixture
def su_headers(client, db):
    """Получение токена и формирование headers для суперюзера"""
    admin = UserFactory(email='admin@ya.ru', password='password',
                        is_superuser=True)

    json = {
        'email': admin.email,
        'password': 'password'
    }

    response = client.post('/api/v1/auth/login/', json=json)

    access_token = response.json.get('access_token')

    headers = {'Authorization': f'Bearer {access_token}'}

    return headers


@pytest.fixture
def get_headers(client):

    def inner(user):

        json = {
            'email': user.email,
            'password': 'password'
        }

        response = client.post('/api/v1/auth/login/', json=json)

        access_token = response.json.get('access_token')

        _headers = {'Authorization': f'Bearer {access_token}'}

        return _headers
    return inner


class General:

    base_url = ''

    def compile_url(self, *args, tail_slash=True):
        url = '/'.join(str(arg) for arg in args)
        if tail_slash:
            return self.base_url + url + '/'
        return self.base_url + url

    @pytest.fixture(autouse=True)
    def clear_table(self, db):
        db.session.query(RolesUsers).delete()
        db.session.query(Journal).delete()
        db.session.query(Profile).delete()
        db.session.query(User).delete()
        db.session.query(Role).delete()
        db.session.commit()


class TestRBACUsers(General):

    base_url = '/api/v1/rbac/users/'

    def test_01_smoke(self, client, db, su_headers):

        response = client.get(self.base_url, headers=su_headers)
        assert response.status_code == HTTPStatus.OK

    def test_02_get_user(self, client, db, su_headers):

        num = 10

        new_users = UserFactory.create_batch(num)

        response = client.get(self.base_url, headers=su_headers)

        # суперюзер уже создан, поэтому в базе будет на одного юзер больше
        assert len(response.json) == num + 1

        for user in new_users:
            expected = {'id': str(user.id), 'email': user.email}
            assert expected in response.json, (
                f'Не найден пользователь со следующими данными {expected}'
            )

    def test_03_without_token(self, db, client):
        response = client.get(self.base_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_04_without_permission(self, client, db, get_headers):
        user = UserFactory()
        headers = get_headers(user)
        response = client.get(self.base_url, headers=headers)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_05_get_roles_for_user(self, client, db, su_headers):

        num = 10
        user = UserFactory()
        roles = RoleFactory.create_batch(num)
        db.session.flush()

        data = [
            RolesUsers(user_id=user.id, role_id=role.id) for role in roles
        ]

        db.session.add_all(data)
        db.session.commit()

        url = self.compile_url(user.id, 'roles')
        response = client.get(url, headers=su_headers)

        assert len(response.json) == num

        for role in roles:
            expected = {'id': str(role.id), 'name': role.name}

            assert expected in response.json, (
                f'Не найдена роль со следующими данными {expected}'
            )

    def test_06_roles_for_fake_users(self, client, db, su_headers):

        fake_user_id = uuid.uuid4()

        url = self.compile_url(fake_user_id, 'roles')
        response = client.get(url, headers=su_headers)

        assert 'error' in response.json
        assert 'User not found' == response.json.get('msg')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_07_revoke_roles_from_user(self, client, db, su_headers):

        num = 10
        roles = RoleFactory.create_batch(num)
        user = UserFactory()
        db.session.flush()

        data = [
            RolesUsers(user_id=user.id, role_id=role.id) for role in roles
        ]

        db.session.add_all(data)
        db.session.commit()

        body = {
            'roles': [role.id for role in roles]
        }

        url = self.compile_url(user.id, 'roles')

        response = client.get(url, headers=su_headers)
        assert len(response.json) == num

        response = client.delete(url, headers=su_headers, json=body)

        expected_msg = 'Roles removed from user'
        assert expected_msg == response.json.get('msg')
        assert RolesUsers.query.filter_by(user_id=user.id).count() == 0

        response = client.get(url, headers=su_headers)
        assert len(response.json) == 0

    def test_08_revoke_roles_from_fake_user(self, client, db, su_headers):

        fake_user_id = uuid.uuid4()

        url = self.compile_url(fake_user_id, 'roles')

        body = {
            'roles': [str(uuid.uuid4()) for _ in range(10)]
        }

        response = client.delete(url, headers=su_headers, json=body)

        assert 'error' in response.json
        assert 'User not found' == response.json.get('msg')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_09_add_roles_to_user(self, client, db, su_headers):

        num = 10
        roles = RoleFactory.create_batch(num)
        user = UserFactory()

        db.session.flush()

        body = {
            'roles': [role.id for role in roles]
        }

        url = self.compile_url(user.id, 'roles')

        response = client.get(url, headers=su_headers)
        assert len(response.json) == 0

        response = client.post(url, headers=su_headers, json=body)

        expected_msg = 'Role added to user'
        assert expected_msg == response.json.get('msg')
        assert RolesUsers.query.filter_by(user_id=user.id).count() == num

        response = client.get(url, headers=su_headers)
        assert len(response.json) == num

    def test_10_add_roles_to_fake_users(self, client, db, su_headers):

        fake_user_id = uuid.uuid4()

        url = self.compile_url(fake_user_id, 'roles')

        body = {
            'roles': [str(uuid.uuid4()) for _ in range(10)]
        }

        response = client.post(url, headers=su_headers, json=body)

        assert 'error' in response.json
        assert 'User not found' == response.json.get('msg')
        assert response.status_code == HTTPStatus.NOT_FOUND


class TestRBACRoles(General):

    base_url = '/api/v1/rbac/roles/'

    def test_01_smoke(self, client, db, su_headers):

        response = client.get(self.base_url, headers=su_headers)
        assert response.status_code == HTTPStatus.OK

    def test_02_create_role(self, client, db, su_headers):

        body = {
            'name': 'role_1',
            'description': 'some text'
        }

        response = client.post(self.base_url, headers=su_headers, json=body)

        assert response.status_code == HTTPStatus.CREATED
        assert 'Role created' in response.json.get('msg')

        roles = Role.query.all()
        assert len(roles) == 1

        role = Role.query.first()

        assert role.name == 'role_1'
        assert role.description == 'some text'

    def test_03_create_role_without_auth(self, client, db):

        body = {
            'name': 'some_role',
            'description': 'some text'
        }

        response = client.post(self.base_url, json=body)
        assert response.status_code == HTTPStatus.UNAUTHORIZED

    def test_04_create_role_with_same_name(self, client, db, su_headers):

        role = RoleFactory()

        body = {
            'name': role.name,
            'description': role.description
        }

        response = client.post(self.base_url, headers=su_headers, json=body)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        roles = Role.query.all()

        assert len(roles) == 1

    def test_05_get_all_roles(self, client, db, su_headers):

        num = 10

        roles = RoleFactory.create_batch(num)

        response = client.get(self.base_url, headers=su_headers)

        assert len(response.json) == num

        for role in roles:
            expected = {'id': str(role.id), 'name': role.name}

            assert expected in response.json, (
                f'Не найдена роль со следующими данными {expected}'
            )

    def test_06_users_with_roles(self, client, db, su_headers):

        num = 10

        role = RoleFactory()
        users = UserFactory.create_batch(num)
        db.session.flush()

        data = [
            RolesUsers(user_id=user.id, role_id=role.id) for user in users
        ]

        db.session.add_all(data)
        db.session.commit()

        url = self.compile_url(role.id, 'users')
        response = client.get(url, headers=su_headers)

        assert len(response.json) == num

        for user in users:
            expected = {'id': str(user.id), 'email': user.email}

            assert expected in response.json, (
                f'Не найден юзер со следующими данными {expected}'
            )

    def test_07_users_for_fake_role(self, client, db, su_headers):

        fake_role_id = uuid.uuid4()

        url = self.compile_url(fake_role_id, 'users')
        response = client.get(url, headers=su_headers)

        assert 'error' in response.json
        assert 'Role not found' == response.json.get('msg')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_08_revoke_role_from_users(self, client, db, su_headers):

        num = 10
        role = RoleFactory()
        users = UserFactory.create_batch(num)
        db.session.flush()

        data = [
            RolesUsers(user_id=user.id, role_id=role.id) for user in users
        ]

        db.session.add_all(data)
        db.session.commit()

        body = {
            'users': [user.id for user in users]
        }

        url = self.compile_url(role.id, 'users')

        response = client.get(url, headers=su_headers)
        assert len(response.json) == num

        response = client.delete(url, headers=su_headers, json=body)

        expected_msg = f'Role "{role.name}" removed from users'
        assert expected_msg == response.json.get('msg')
        assert RolesUsers.query.filter_by(role_id=role.id).count() == 0

        response = client.get(url, headers=su_headers)
        assert len(response.json) == 0

    def test_09_revoke_fake_role_from_users(self, client, db, su_headers):

        fake_role_id = uuid.uuid4()

        url = self.compile_url(fake_role_id, 'users')

        body = {
            'users': [str(uuid.uuid4()) for _ in range(10)]
        }

        response = client.delete(url, headers=su_headers, json=body)

        assert 'error' in response.json
        assert 'Role not found' == response.json.get('msg')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_10_add_role_to_users(self, client, db, su_headers):

        num = 10
        role = RoleFactory()
        users = UserFactory.create_batch(num)
        db.session.flush()

        body = {
            'users': [user.id for user in users]
        }

        url = self.compile_url(role.id, 'users')

        response = client.get(url, headers=su_headers)
        assert len(response.json) == 0

        response = client.post(url, headers=su_headers, json=body)

        expected_msg = f'Role "{role.name}" added to users'
        assert expected_msg == response.json.get('msg')
        assert RolesUsers.query.filter_by(role_id=role.id).count() == num

        response = client.get(url, headers=su_headers)
        assert len(response.json) == num

    def test_11_add_fake_role_to_users(self, client, db, su_headers):

        fake_role_id = uuid.uuid4()

        url = self.compile_url(fake_role_id, 'users')

        body = {
            'users': [str(uuid.uuid4()) for _ in range(10)]
        }

        response = client.post(url, headers=su_headers, json=body)

        assert 'error' in response.json
        assert 'Role not found' == response.json.get('msg')
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_12_update_role(self, client, db, su_headers):

        role = RoleFactory(name='Original_name',
                           description='Original Description')
        db.session.flush()

        role_from_db = Role.query.get(role.id)

        assert role == role_from_db

        url = self.compile_url(role.id, tail_slash=False)

        body = {
            'name': 'Updated name',
            'description': 'Updated Description'
        }

        response = client.patch(url, headers=su_headers, json=body)

        assert response.status_code == HTTPStatus.OK

        updated_role_from_db = Role.query.get(role.id)

        assert updated_role_from_db.name == 'Updated name'
        assert updated_role_from_db.description == 'Updated Description'

    def test_13_update_role_with_existed_name(self, client, db, su_headers):

        original_role = RoleFactory(name='Original Role')
        second_role = RoleFactory(name='Second Role')
        db.session.flush()

        url = self.compile_url(second_role.id, tail_slash=False)

        body = {
            'name': original_role.name,
        }

        response = client.patch(url, headers=su_headers, json=body)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        second_role_from_db = Role.query.get(second_role.id)

        assert second_role_from_db.name != original_role.name
        assert second_role_from_db.name == second_role.name

    def test_14_delete_role(self, client, db, su_headers):

        role = RoleFactory()
        db.session.flush()

        role_from_db = Role.query.get(role.id)

        assert role_from_db == role

        url = self.compile_url(role.id, tail_slash=False)

        response = client.delete(url, headers=su_headers)

        assert response.status_code == HTTPStatus.NO_CONTENT

        role_from_db = Role.query.get(role.id)

        assert role_from_db is None
