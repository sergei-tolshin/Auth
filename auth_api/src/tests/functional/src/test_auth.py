import pytest
from flask_jwt_extended import decode_token
from freezegun import freeze_time
from tests.functional.testdata.factories import UserFactory


class TestAuth(object):
    pytest.shared = {}

    @pytest.mark.dependency()
    def test_01_user_login(self, client, db):
        user = UserFactory()
        user_data = {
            'email': user.email,
            'password': 'password'
        }
        response = client.post('/api/v1/auth/login/', json=user_data)
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        assert 'access_token' in response.json, \
            'В ответе должен быть параметр `access_token`'
        assert 'refresh_token' in response.json, \
            'В ответе должен быть параметр `refresh_token`'

        pytest.shared['token_pair'] = response.json
        pytest.shared['user'] = user_data

    @pytest.mark.dependency(depends=['TestAuth::test_01_user_login'])
    def test_02_token_verify(self, client, db):
        access_token = pytest.shared['token_pair']['access_token']
        response = client.post(
            '/api/v1/auth/token/verify/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        assert response.json['msg'] == 'The token has been verified', \
            'В ответе должно быть сообщение'

    @pytest.mark.dependency(depends=['TestAuth::test_01_user_login'])
    def test_03_token_refresh(self, client, db):
        access_token = pytest.shared['token_pair']['access_token']
        refresh_token = pytest.shared['token_pair']['refresh_token']
        response = client.post(
            '/api/v1/auth/token/refresh/',
            json={'refresh_token': refresh_token})
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        assert 'access_token' in response.json, \
            'В ответе должен быть параметр `access_token`'
        assert 'refresh_token' in response.json, \
            'В ответе должен быть параметр `refresh_token`'
        assert access_token != response.json['access_token'], \
            'В ответе должен быть новый `access_token` '
        assert refresh_token != response.json['refresh_token'], \
            'В ответе должен быть новый `refresh_token` '

        pytest.shared['new_token_pair'] = response.json

    @pytest.mark.dependency(depends=['TestAuth::test_03_token_refresh'])
    def test_04_user_old_token(self, client, db):
        access_token = pytest.shared['token_pair']['access_token']
        response = client.get(
            '/api/v1/account/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 403, \
            'Со старым access_token возвращается статус 403'

    @pytest.mark.dependency(depends=['TestAuth::test_03_token_refresh'])
    def test_05_user_logout(self, client, db):
        access_token = pytest.shared['new_token_pair']['access_token']
        response = client.delete(
            '/api/v1/auth/logout/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'

    @pytest.mark.dependency(depends=['TestAuth::test_05_user_logout'])
    def test_06_user_unauthorized(self, client, db):
        access_token = pytest.shared['new_token_pair']['access_token']
        response = client.get(
            '/api/v1/account/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 401, \
            'Неавторизованный пользователь не может зайти в закрытые разделы'

    def test_07_user_unregistered(self, client, db):
        json = {
            'email': 'unregistered@fake.fake',
            'password': 'password'
        }
        response = client.post('/api/v1/auth/login/', json=json)

        assert response.status_code == 404, \
            'Проверьте, что при запросе возвращается статус 404'
        assert response.json['msg'] == 'Invalid email or password', \
            'В ответе должно быть сообщение'

    def test_08_access_token_revoke(self, client, db, cache):
        user = pytest.shared['user']
        response = client.post('/api/v1/auth/login/', json=user)
        access_token = response.json['access_token']
        response = client.get(
            '/api/v1/account/journal/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        user_id = decode_token(access_token)['sub']
        rti = decode_token(access_token)['rti']
        cache.delete(f'user:{user_id}:{rti}')
        response = client.get(
            '/api/v1/account/journal/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 403, \
            'Проверьте, что при запросе возвращается статус 403' \
            'Невозможно войти с отозванным токеном'

    @freeze_time('2022-04-23 00:00', as_kwarg='frozen_time')
    def test_09_access_token_expired(self, client, **kwargs):
        user = pytest.shared['user']
        response = client.post('/api/v1/auth/login/', json=user)
        access_token = response.json['access_token']
        response = client.get(
            '/api/v1/account/journal/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 200, \
            'Проверьте, что при запросе возвращается статус 200'
        kwargs.get('frozen_time').move_to('2022-04-23 00:16')
        response = client.get(
            '/api/v1/account/journal/',
            headers={'Authorization': f'Bearer {access_token}'})
        assert response.status_code == 401, \
            'Проверьте, что при запросе возвращается статус 401'
        assert response.json['msg'] == 'Token has expired', \
            'В ответе есть сообщение об истечении срока действия токена'
