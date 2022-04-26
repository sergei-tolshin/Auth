import pytest
from app.models.user import User
from flask_jwt_extended import decode_token
from tests.functional.testdata.factories import (ChangeEmailFactory,
                                                 ChangePasswordFactory,
                                                 ProfileFactory,
                                                 RegisterUserFactory)


class TestAccount(object):
    pytest.shared = {}

    @pytest.mark.dependency()
    def test_01_register_user(self, client, db, cache):
        new_user = RegisterUserFactory()
        pytest.shared['user'] = new_user
        response = client.post('/api/v1/account/register/', json=new_user)

        assert response.status_code == 201, \
            'Проверьте, что при запросе возвращается статус 201'
        assert 'id' in response.json, \
            'В ответе должен быть параметр `id`'

        user = User.find_by_email(new_user['email'])
        assert response.json['id'] == str(user.id), \
            'ID в ответе должно совпадать с ID в базе '

    @pytest.mark.dependency(depends=['TestAccount::test_01_register_user'])
    def test_02_user_already_exists(self, client, db, cache):
        user = pytest.shared['user']
        response = client.post('/api/v1/account/register/', json=user)
        assert response.status_code == 422, \
            'Проверьте, что при запросе возвращается статус 422' \
            'Невозможно зарегистрироваться с повторяющимся email'

    @pytest.mark.dependency(depends=['TestAccount::test_01_register_user'])
    def test_03_profile_edit(self, client, db, cache):
        user = pytest.shared['user']
        response = client.post('/api/v1/auth/login/', json=user)
        access_token = response.json['access_token']
        pytest.shared['access_token'] = access_token
        data = ProfileFactory()
        response = client.patch(
            '/api/v1/account/',
            headers={'Authorization': f'Bearer {access_token}'},
            json=data
        )
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        profiel = User.find_by_email(user['email']).profile
        first_name = profiel.first_name
        assert data['first_name'] == first_name, \
            'Проверьте, что данные сохраняются'

        edit_data = {'first_name': 'Newname'}
        response = client.patch(
            '/api/v1/account/',
            headers={'Authorization': f'Bearer {access_token}'},
            json=edit_data
        )

        edit_profile = User.find_by_email(user['email']).profile
        assert first_name != edit_profile.first_name, \
            'Проверьте, что данные изменились'

    @pytest.mark.dependency(depends=['TestAccount::test_01_register_user'])
    def test_04_journal(self, client, db, cache):
        access_token = pytest.shared['access_token']
        response = client.get(
            '/api/v1/account/journal/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        assert type(response.json) == list, \
            'Тип данных должен быть список'

        data = response.json[0]
        assert 'id' in data, \
            'Не найден параметр `id`'
        assert 'action' in data, \
            'Не найден параметр `action`'
        assert 'ip' in data, \
            'Не найден параметр `ip`'
        assert 'user_agent' in data, \
            'Не найден параметр `user_agent`'
        assert 'created' in data, \
            'Не найден параметр `created`'

    @pytest.mark.dependency(depends=['TestAccount::test_01_register_user'])
    def test_05_change_password(self, client, db, cache):
        user = pytest.shared['user']
        access_token = pytest.shared['access_token']
        for i in range(3):
            client.post('/api/v1/auth/login/', json=user)
        user_id = User.find_by_email(user['email']).id
        sessions_before = cache.keys(f'user:{user_id}:*')
        data = ChangePasswordFactory(current_password=user['password'])
        response = client.post(
            '/api/v1/account/change-password/',
            headers={'Authorization': f'Bearer {access_token}'},
            json=data)
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        sessions_after = cache.keys(f'user:{user_id}:*')
        assert len(sessions_before) != len(sessions_after)
        assert len(sessions_after) == 1, \
            'Проверьте, что осталась только одна активная сессия'

        response = client.post('/api/v1/auth/login/', json=user)
        assert response.status_code == 404, \
            'Проверьте, что невозможно зайти со старым паролем'
        user['password'] = data['new_password']
        response = client.post('/api/v1/auth/login/', json=user)
        assert response.status_code == 200, \
            'Проверьте, что можно зайти с новым паролем'

    @pytest.mark.dependency(depends=['TestAccount::test_05_change_password'])
    def test_06_change_email(self, client, db, cache):
        user = pytest.shared['user']
        access_token = pytest.shared['access_token']
        for i in range(3):
            client.post('/api/v1/auth/login/', json=user)
        user_id = User.find_by_email(user['email']).id
        sessions_before = cache.keys(f'user:{user_id}:*')
        data = ChangeEmailFactory(current_email=user['email'])
        response = client.post(
            '/api/v1/account/change-email/',
            headers={'Authorization': f'Bearer {access_token}'},
            json=data)
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        sessions_after = cache.keys(f'user:{user_id}:*')
        assert len(sessions_before) != len(sessions_after)
        assert len(sessions_after) == 1, \
            'Проверьте, что осталась только одна активная сессия(текущая)'

        response = client.post('/api/v1/auth/login/', json=user)
        assert response.status_code == 404, \
            'Проверьте, что невозможно зайти со старым email'
        user['email'] = data['new_email']
        response = client.post('/api/v1/auth/login/', json=user)
        assert response.status_code == 200, \
            'Проверьте, что можно зайти с новым email'

    @pytest.mark.dependency(depends=['TestAccount::test_06_change_email'])
    def test_07_sessions(self, client, db, cache):
        access_token = pytest.shared['access_token']
        response = client.get(
            '/api/v1/account/sessions/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        assert type(response.json) == list, \
            'Тип данных должен быть список'

        data = response.json[0]
        assert 'id' in data, \
            'Не найден параметр `id`'
        assert 'ip' in data, \
            'Не найден параметр `ip`'
        assert 'user_agent' in data, \
            'Не найден параметр `user_agent`'
        assert 'last_activity' in data, \
            'Не найден параметр `last_activity`'

    @pytest.mark.dependency(depends=['TestAccount::test_06_change_email'])
    def test_08_sessions_detail(self, client, db, cache):
        access_token = pytest.shared['access_token']
        response = client.get(
            '/api/v1/account/sessions/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        session_id = response.json[0]['id']
        response = client.get(
            f'/api/v1/account/sessions/{session_id}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        assert type(response.json) == dict, \
            'Тип данных должен быть словарь'

        data = response.json
        assert 'id' in data, \
            'Не найден параметр `id`'
        assert 'ip' in data, \
            'Не найден параметр `ip`'
        assert 'user_agent' in data, \
            'Не найден параметр `user_agent`'
        assert 'last_activity' in data, \
            'Не найден параметр `last_activity`'

    @pytest.mark.dependency(depends=['TestAccount::test_06_change_email'])
    def test_09_sessions_delete(self, client, db, cache):
        access_token = pytest.shared['access_token']
        rti = decode_token(access_token)['rti']
        response = client.get(
            '/api/v1/account/sessions/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        sessions = response.json
        for session in sessions:
            if session['id'] != rti:
                session_id = session['id']
                break
        response = client.delete(
            f'/api/v1/account/sessions/{session_id}',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 204, \
            'Проверьте, что при запросе возвращается статус 204'
        response = client.get(
            '/api/v1/account/sessions/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert session not in response.json, \
            'Проверьте, что сессия удаляется'

    @pytest.mark.dependency(depends=['TestAccount::test_06_change_email'])
    def test_10_sessions_delete_all(self, client, db, cache):
        user = pytest.shared['user']
        access_token = pytest.shared['access_token']
        for i in range(3):
            client.post('/api/v1/auth/login/', json=user)
        response = client.get(
            '/api/v1/account/sessions/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert len(response.json) > 1, \
            'Проверьте, что активных сессий больше 1'
        response = client.delete(
            '/api/v1/account/sessions/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        response = client.get(
            '/api/v1/account/sessions/',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert len(response.json) == 1, \
            'Проверьте, что осталась только одна активная сессия'
