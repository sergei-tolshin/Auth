import uuid
from http import HTTPStatus

import pytest

from functional.settings import config
from functional.testdata.genres.factory import GenreFactory, GenreDetailFactory
from functional.testdata.genres.schema import SCHEMA as genres_schema


GENRE_INDEX = config.ELASTIC_INDEX['genres']


@pytest.fixture(scope='class')
async def genres_index(es_client):
    await es_client.indices.create(index=GENRE_INDEX, body=genres_schema)
    yield
    await es_client.indices.delete(index=GENRE_INDEX)


@pytest.mark.usefixtures('genres_index')
class TestGenreAPI:

    path = 'api/v1/genres/'

    @property
    def params(self):
        return {'sort': 'name', 'page[size]': 10, 'page[number]': 1}

    @pytest.fixture(autouse=True)
    async def clear_storage(self, es_client):
        query = {"query": {"match_all": {}}}
        await es_client.delete_by_query(index=GENRE_INDEX, body=query,
                                        refresh=True)

    @pytest.fixture(autouse=True)
    async def clear_cache(self, cache):
        await cache.flushall()

    @pytest.mark.asyncio
    async def test_genres_smoke(self, make_get_request):
        response = await make_get_request(self.path, self.params)
        assert response.status == HTTPStatus.OK

    @pytest.mark.asyncio
    async def test_genres_sort_asc(self, bulk, make_get_request):

        genres = GenreFactory.build_batch(10)
        await bulk(index=GENRE_INDEX, objects=genres)

        response = await make_get_request(self.path, self.params)
        results = [record['name'] for record in response.body['results']]

        expected = sorted([genre.name for genre in genres])
        assert results == expected

    @pytest.mark.asyncio
    async def test_genres_sort_desc(self, bulk, make_get_request):

        genres = GenreFactory.build_batch(10)
        await bulk(index=GENRE_INDEX, objects=genres)

        params = self.params
        params['sort'] = '-name'
        response = await make_get_request(self.path, params=params)
        results = [record['name'] for record in response.body['results']]

        expected = sorted([genre.name for genre in genres], reverse=True)
        assert results == expected

    @pytest.mark.asyncio
    async def test_genres_page_number_0(self, make_get_request):
        params = self.params
        params['page[number]'] = 0
        response = await make_get_request(self.path, params=params)

        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'page[number]' in details['loc']
        assert ('ensure this value is greater than or equal to 1' ==
                details['msg'])

    @pytest.mark.asyncio
    async def test_genres_page_size_0(self, make_get_request):
        params = self.params
        params['page[size]'] = 0
        response = await make_get_request(self.path, params=params)
        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'page[size]' in details['loc']
        assert ('ensure this value is greater than or equal to 1' ==
                details['msg'])

    @pytest.mark.asyncio
    async def test_genres_page_size_1000(self, make_get_request):
        params = self.params
        params['page[size]'] = 1000
        response = await make_get_request(self.path, params=params)

        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'page[size]' in details['loc']
        assert ('ensure this value is less than or equal to 100' ==
                details['msg'])

    @pytest.mark.asyncio
    async def test_genres_by_id(self, bulk, make_get_request):
        genre = GenreDetailFactory()
        await bulk(index=GENRE_INDEX, objects=[genre])
        path = self.path + genre.id
        response = await make_get_request(path)
        assert response.body == genre.dict()

    @pytest.mark.asyncio
    async def test_genres_by_not_exist_id(self, bulk, make_get_request):
        genre = GenreDetailFactory()
        await bulk(index=GENRE_INDEX, objects=[genre])
        fake_id = str(uuid.uuid4())
        path = self.path + fake_id
        response = await make_get_request(path)
        assert fake_id != genre.id
        assert response.status == HTTPStatus.NOT_FOUND

    @pytest.mark.asyncio
    async def test_cache_update_genre(self, bulk, make_get_request, cache):
        genre = GenreDetailFactory(name='original',
                                   description='original genre')
        await bulk(index=GENRE_INDEX, objects=[genre])
        path = self.path + genre.id

        response = await make_get_request(path)
        assert response.body == genre.dict()

        genre.name = 'updated'
        genre.description = 'updated genre'
        await bulk(index=GENRE_INDEX, objects=[genre])

        response = await make_get_request(path)
        assert response.body != genre.dict()

        await cache.flushall()
        response = await make_get_request(path)
        assert response.body == genre.dict()

    @pytest.mark.asyncio
    async def test_cache_delete_genre(self, bulk, make_get_request, cache):
        genre = GenreDetailFactory(name='original',
                                   description='original genre')
        await bulk(index=GENRE_INDEX, objects=[genre])
        path = self.path + genre.id

        response = await make_get_request(path)
        assert response.body == genre.dict()

        await bulk(index=GENRE_INDEX, objects=[genre], op_type='delete')

        response = await make_get_request(path)
        assert response.body == genre.dict()

        await cache.flushall()
        response = await make_get_request(path)
        assert 'detail' in response.body
        assert (response.body['detail'] == 'жанр не найден' or
                response.body['detail'] == 'Genres not found')

    @pytest.mark.asyncio
    async def test_genres_sort_other_field(self, bulk, make_get_request):

        genres = GenreFactory.build_batch(10)
        await bulk(index=GENRE_INDEX, objects=genres)

        params = self.params
        params['sort'] = '-description'
        response = await make_get_request(self.path, params=params)

        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'sort' in details['loc']
        assert ('value is not a valid enumeration member' in
                details['msg'])

    @pytest.mark.asyncio
    async def test_genres_page_size(self, make_get_request, bulk):

        page_size = self.params['page[size]']
        pages = 10

        genres = GenreFactory.build_batch(page_size * pages - page_size // 2)
        await bulk(index=GENRE_INDEX, objects=genres)

        params = self.params
        for num in range(1, pages + 1):
            params['page[number]'] = num
            response = await make_get_request(self.path, params=params)
            assert len(response.body['results']) <= page_size

    @pytest.mark.asyncio
    async def test_genres_page_numbers(self, make_get_request, bulk):

        page_size = self.params['page[size]']

        genres = GenreFactory.build_batch(page_size * 2)
        await bulk(index=GENRE_INDEX, objects=genres)

        response = await make_get_request(self.path, params=self.params)
        first_page_body = response.body['results']
        sorted_genres = sorted(genres, key=lambda obj: obj.name)

        assert sorted_genres[0].dict() in first_page_body

        params = self.params
        params['page[number]'] = 2

        response = await make_get_request(self.path, params=params)
        second_page_body = response.body['results']

        assert sorted_genres[-1].dict() in second_page_body

        assert first_page_body != second_page_body

        params['page[number]'] = 3
        response = await make_get_request(self.path, params=params)

        details = response.body['detail']

        assert details == 'Invalid page'
