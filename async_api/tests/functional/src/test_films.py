import uuid
from http import HTTPStatus

import pytest

from functional.settings import config
from functional.testdata.films.factories import FilmFactory, FilmDetailFactory
from functional.testdata.genres.factory import GenreFactory
from functional.testdata.films.schema import SCHEMA as films_schema


FILM_INDEX = config.ELASTIC_INDEX['films']


@pytest.fixture(scope='class')
async def create_index(es_client):
    await es_client.indices.create(index=FILM_INDEX, body=films_schema)
    yield
    await es_client.indices.delete(index=FILM_INDEX)


@pytest.mark.usefixtures('create_index')
class TestFilmsAPI:

    path = 'api/v1/films/'

    @property
    def params(self):
        return {'sort': '-imdb_rating', 'page[size]': 10, 'page[number]': 1}

    @pytest.fixture(autouse=True)
    async def clear_storage(self, es_client):
        query = {"query": {"match_all": {}}}
        await es_client.delete_by_query(index=FILM_INDEX, body=query,
                                        refresh=True)

    @pytest.fixture(autouse=True)
    async def clear_cache(self, cache):
        await cache.flushall()

    @pytest.mark.asyncio
    async def test_films_smoke(self, make_get_request):
        response = await make_get_request(self.path, self.params)
        assert response.status == HTTPStatus.OK

    @pytest.mark.asyncio
    async def test_films_sort_desc(self, bulk, make_get_request):

        films = FilmFactory.build_batch(10)
        await bulk(index=FILM_INDEX, objects=films)

        response = await make_get_request(self.path, self.params)
        results = [record['imdb_rating']
                   for record in response.body['results']]

        expected = sorted([film.imdb_rating for film in films], reverse=True)
        assert results == expected

    @pytest.mark.asyncio
    async def test_films_sort_asc(self, bulk, make_get_request):

        films = FilmFactory.build_batch(10)
        await bulk(index=FILM_INDEX, objects=films)

        params = self.params
        params['sort'] = 'imdb_rating'
        response = await make_get_request(self.path, params=params)
        results = [record['imdb_rating']
                   for record in response.body['results']]

        expected = sorted([film.imdb_rating for film in films])
        assert results == expected

    @pytest.mark.asyncio
    async def test_films_page_number_0(self, make_get_request):
        params = self.params
        params['page[number]'] = 0
        response = await make_get_request(self.path, params=params)

        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'page[number]' in details['loc']
        assert ('ensure this value is greater than or equal to 1' ==
                details['msg'])

    @pytest.mark.asyncio
    async def test_films_page_size_0(self, make_get_request):
        params = self.params
        params['page[size]'] = 0
        response = await make_get_request(self.path, params=params)
        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'page[size]' in details['loc']
        assert ('ensure this value is greater than or equal to 1' ==
                details['msg'])

    @pytest.mark.asyncio
    async def test_films_page_size_1000(self, make_get_request):
        params = self.params
        params['page[size]'] = 1000
        response = await make_get_request(self.path, params=params)

        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'page[size]' in details['loc']
        assert ('ensure this value is less than or equal to 100' ==
                details['msg'])

    @pytest.mark.asyncio
    async def test_film_by_id(self, bulk, make_get_request):
        film = FilmDetailFactory()
        await bulk(index=FILM_INDEX, objects=[film])
        path = self.path + film.id
        response = await make_get_request(path)
        assert response.body == film.dict()

    @pytest.mark.asyncio
    async def test_film_by_not_exist_id(self, bulk, make_get_request):
        film = FilmDetailFactory()
        await bulk(index=FILM_INDEX, objects=[film])
        fake_id = str(uuid.uuid4())
        path = self.path + fake_id
        response = await make_get_request(path)
        assert fake_id != film.id
        assert response.status == HTTPStatus.NOT_FOUND

    @pytest.mark.asyncio
    async def test_cache_update_film(self, bulk, make_get_request, cache):
        film = FilmDetailFactory(title='original title',
                                 description='original film')
        await bulk(index=FILM_INDEX, objects=[film])
        path = self.path + film.id

        response = await make_get_request(path)
        assert response.body == film.dict()

        film.title = 'updated title'
        film.description = 'updated film'
        await bulk(index=FILM_INDEX, objects=[film])

        response = await make_get_request(path)
        assert response.body != film.dict()

        await cache.flushall()
        response = await make_get_request(path)
        assert response.body == film.dict()

    @pytest.mark.asyncio
    async def test_cache_delete_film(self, bulk, make_get_request, cache):
        film = FilmDetailFactory(name='original title',
                                 description='original film')
        await bulk(index=FILM_INDEX, objects=[film])
        path = self.path + film.id

        response = await make_get_request(path)
        assert response.body == film.dict()

        await bulk(index=FILM_INDEX, objects=[film], op_type='delete')

        response = await make_get_request(path)
        assert response.body == film.dict()

        await cache.flushall()
        response = await make_get_request(path)
        assert 'detail' in response.body
        assert (response.body['detail'] == 'фильм не найден' or
                response.body['detail'] == 'Films not found')

    @pytest.mark.asyncio
    async def test_films_sort_other_field(self, bulk, make_get_request):

        films = FilmFactory.build_batch(10)
        await bulk(index=FILM_INDEX, objects=films)

        params = self.params
        params['sort'] = '-title'
        response = await make_get_request(self.path, params=params)

        details = response.body['detail'][0]

        assert 'msg' in details
        assert 'sort' in details['loc']
        assert ('value is not a valid enumeration member' in
                details['msg'])

    @pytest.mark.asyncio
    async def test_films_page_size(self, make_get_request, bulk):

        page_size = self.params['page[size]']
        pages = 10

        films = FilmFactory.build_batch(page_size * pages - page_size // 2)
        await bulk(index=FILM_INDEX, objects=films)

        params = self.params
        for num in range(1, pages + 1):
            params['page[number]'] = num
            response = await make_get_request(self.path, params=params)
            assert len(response.body['results']) <= page_size

    @pytest.mark.asyncio
    async def test_films_page_numbers(self, make_get_request, bulk):

        page_size = self.params['page[size]']

        films = FilmFactory.build_batch(page_size * 2)
        await bulk(index=FILM_INDEX, objects=films)

        response = await make_get_request(self.path, params=self.params)
        first_page_body = response.body['results']
        sorted_films = sorted(
            films, key=lambda obj: obj.imdb_rating, reverse=True)

        assert sorted_films[0].dict() in first_page_body

        params = self.params
        params['page[number]'] = 2

        response = await make_get_request(self.path, params=params)
        second_page_body = response.body['results']

        assert sorted_films[-1].dict() in second_page_body

        assert first_page_body != second_page_body

        params['page[number]'] = 3
        response = await make_get_request(self.path, params=params)

        details = response.body['detail']

        assert details == 'Invalid page'

    @pytest.mark.asyncio
    async def test_films_filter_single_genre(self, make_get_request, bulk):
        genre_one = GenreFactory()
        genre_one_num = 10
        genre_two = GenreFactory()
        genre_two_num = 1
        films_with_genre_one = FilmDetailFactory.build_batch(
            genre_one_num, genre=[genre_one])
        films_with_genre_two = FilmDetailFactory.build_batch(
            genre_two_num, genre=[genre_two])
        films = films_with_genre_one + films_with_genre_two
        await bulk(index=FILM_INDEX, objects=films)
        params = self.params
        params['filter[genre]'] = genre_one.id
        response = await make_get_request(self.path, params=params)
        assert len(response.body['results']) == genre_one_num

        params['filter[genre]'] = genre_two.id
        response = await make_get_request(self.path, params=params)
        assert len(response.body['results']) == genre_two_num

    @pytest.mark.asyncio
    async def test_films_filter_multi_genres(self, make_get_request, bulk):
        genre_one = GenreFactory()
        genre_two = GenreFactory()
        films_one_genre = 5
        films_multi_genres = 5
        films_with_genre_one = FilmDetailFactory.build_batch(
            films_one_genre, genre=[genre_one])
        films_with_genre_two = FilmDetailFactory.build_batch(
            films_multi_genres, genre=[genre_one, genre_two])
        films = films_with_genre_one + films_with_genre_two
        await bulk(index=FILM_INDEX, objects=films)
        params = self.params
        params['filter[genre]'] = genre_one.id
        response = await make_get_request(self.path, params=params)
        assert (len(response.body['results']) ==
                films_one_genre + films_multi_genres)

        params['filter[genre]'] = genre_two.id
        response = await make_get_request(self.path, params=params)
        assert len(response.body['results']) == films_multi_genres

    @pytest.mark.asyncio
    async def test_films_filter_not_existed_genre(self, make_get_request, bulk):

        genre = GenreFactory()
        films = FilmDetailFactory.build_batch(10, genre=[genre])
        await bulk(index=FILM_INDEX, objects=films)
        params = self.params
        params['filter[genre]'] = genre.id
        response = await make_get_request(self.path, params=params)
        assert len(response.body['results']) == 10

        fake_genre_id = str(uuid.uuid4)
        params['filter[genre]'] = fake_genre_id
        response = await make_get_request(self.path, params=params)
        assert len(response.body['results']) == 0
