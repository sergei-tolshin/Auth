import math

import orjson
import pytest
from functional.settings import config
from functional.testdata.films.factories import FilmFactory
from functional.testdata.films.models import FilmPagination
from functional.testdata.films.schema import SCHEMA as films_schema
from functional.testdata.persons.factories import (PersonDetailsFactory,
                                                   PersonFactory)
from functional.testdata.persons.models import (PersonDetailsModel,
                                                PersonPagination)
from functional.testdata.persons.schema import SCHEMA as persons_schema
from functional.utils.utils import hash_key

PERSON_INDEX = config.ELASTIC_INDEX['persons']
FILM_INDEX = config.ELASTIC_INDEX['films']


@pytest.fixture(scope='class')
async def person_index(es_client):
    await es_client.indices.create(index=PERSON_INDEX, body=persons_schema)
    yield
    await es_client.indices.delete(index=PERSON_INDEX)


@pytest.fixture(scope='class')
async def films_index(es_client):
    await es_client.indices.create(index=FILM_INDEX, body=films_schema)
    yield
    await es_client.indices.delete(index=FILM_INDEX)


@pytest.mark.usefixtures('person_index', 'films_index')
class TestPersonsAPI:
    path = '/api/v1/persons/'
    num_build_obj = 10

    @pytest.fixture(autouse=True)
    async def clear_storage(self, es_client):
        query = {"query": {"match_all": {}}}
        await es_client.delete_by_query(index=PERSON_INDEX, body=query,
                                        refresh=True)
        await es_client.delete_by_query(index=FILM_INDEX, body=query,
                                        refresh=True)

    @pytest.fixture(autouse=True)
    async def clear_cache(self, cache):
        await cache.flushdb()

    @pytest.mark.asyncio
    async def test_01_person_status(self, make_get_request):
        response = await make_get_request(self.path)
        assert response.status == 200, \
            'Проверьте, что при GET запросе возвращается статус 200'

    @pytest.mark.asyncio
    async def test_02_person_count(self, make_get_request, bulk):
        persons = PersonFactory.build_batch(self.num_build_obj)
        await bulk(index=PERSON_INDEX, objects=persons)

        response = await make_get_request(self.path)
        data = response.body
        assert data['count'] == self.num_build_obj, \
            'Значение параметра `count` не верное'

    @pytest.mark.asyncio
    async def test_03_person_filter(self, make_get_request, bulk, cache):
        persons = PersonFactory.build_batch(self.num_build_obj)
        count_actors = 0
        count_directors = 0
        count_writers = 0
        for person in persons:
            if 'actor' in person.roles:
                count_actors += 1
            if 'director' in person.roles:
                count_directors += 1
            if 'writer' in person.roles:
                count_writers += 1

        await bulk(index=PERSON_INDEX, objects=persons)

        params = {"filter[role]": "director"}
        response = await make_get_request(self.path, params)
        data = response.body
        assert data['count'] == count_directors, \
            'Результаты фильтруются по `filter[role]` параметру `director`'

        params = {'filter[role]': 'actor'}
        response = await make_get_request(self.path, params)
        data = response.body
        assert data['count'] == count_actors, \
            'Результаты фильтруются по `filter[role]` параметру `actor`'

        params = {'filter[role]': 'writer'}
        response = await make_get_request(self.path, params)
        data = response.body
        assert data['count'] == count_writers, \
            'Результаты фильтруются по `filter[role]` параметру `writer`'

        params = {'filter[role]': 'unknown role'}
        response = await make_get_request(self.path, params)
        assert response.status == 422, \
            'Возвращает статус 422 при неверном фильтре'

    @pytest.mark.asyncio
    async def test_04_person_pagination(self, make_get_request, bulk, cache):
        persons = PersonFactory.build_batch(self.num_build_obj)
        await bulk(index=PERSON_INDEX, objects=persons)

        params = {
            'page[number]': 1,
            'page[size]': 10
        }
        response = await make_get_request(self.path, params)
        data = response.body

        assert PersonPagination(**data), \
            'Данные не соответствуют модели `PersonPagination`'

        assert len(data['results']) == params['page[size]'], \
            'Значение параметра `results` не правильное'

        params['page[size]'] = 6
        total_pages = math.ceil(self.num_build_obj / params['page[size]'])
        params['page[number]'] = total_pages
        response = await make_get_request(self.path, params)
        data = response.body
        assert data['total_pages'] == total_pages, \
            'Изменяется количество сраниц при изменении `page[size]`'

        num_results_last_page = self.num_build_obj % params['page[size]']
        num_results = params['page[size]']
        if num_results_last_page != 0:
            num_results = num_results_last_page
        assert len(data['results']) == num_results, \
            'Значение параметра `results` последней страницы не правильное'

        params['page[number]'] = 0
        response = await make_get_request(self.path, params)
        assert response.status == 422, \
            'Статус 422 при неверном `page[number]`'

        page_number = math.ceil(self.num_build_obj / int(params['page[size]']))
        params['page[number]'] = page_number + 1
        response = await make_get_request(self.path, params)
        assert response.status == 404, \
            'Статус 404 при неверном `page[number]`'

        params['page[size]'] = 0
        response = await make_get_request(self.path, params)
        assert response.status == 422, \
            'Статус 422 при неверном `page[size]`'

        params['page[size]'] = 1000
        response = await make_get_request(self.path, params)
        assert response.status == 422, \
            'Статус 422 при неверном `page[size]`'

    """ Поиск конкретного человека """
    @pytest.mark.asyncio
    async def test_05_person_detail(self, make_get_request, bulk, cache):
        person = PersonDetailsFactory()
        await bulk(index=PERSON_INDEX, objects=[person])

        path = f"{self.path}{person.id}/"

        response = await make_get_request(path)
        assert response.status == 200, \
            'Проверьте, что при GET запросе возвращается статус 200'

        data = response.body
        assert PersonDetailsModel(**data), \
            'Данные не соответствуют модели `PersonDetailsModel`'

    @pytest.mark.asyncio
    async def test_06_person_detail_cache(self, make_get_request, bulk, cache):
        person = PersonDetailsFactory()
        await bulk(index=PERSON_INDEX, objects=[person])

        path = f"{self.path}{person.id}/"

        response = await make_get_request(path)
        data = response.body

        key = hash_key(PERSON_INDEX, person.id)
        data_cache = await cache.get(key=key)

        assert await cache.get(key=key) is not None, \
            'Проверьте, что при запросе из кэша возвращаете данные объекта.'
        assert orjson.loads(data_cache) == data, \
            'Данные обекта в elastic не совпадают с данными в кэше'
        await cache.delete(key=key)
        assert await cache.get(key=key) is None, \
            'Проверьте, что при DELETE удаляете объект из кэша'

    @pytest.mark.asyncio
    async def test_07_person_cache_update(self, bulk, make_get_request, cache):
        person = PersonDetailsFactory(full_name='original name')
        await bulk(index=PERSON_INDEX, objects=[person])
        path = self.path + person.id

        response = await make_get_request(path)
        assert response.body == person.dict(), \
            'Проверьте, что возвращенные данные совпадают.'

        person.full_name = 'updated name'
        await bulk(index=PERSON_INDEX, objects=[person])

        response = await make_get_request(path)
        assert response.body != person.dict(), \
            'Проверьте, что данные в elastic и redis не совпадают.'

        await cache.flushall()
        response = await make_get_request(path)
        assert response.body == person.dict(), \
            'Проверьте, что данные обновились.'

    @pytest.mark.asyncio
    async def test_07_person_cache_delete(self, bulk, make_get_request, cache):
        person = PersonDetailsFactory(full_name='original name')
        await bulk(index=PERSON_INDEX, objects=[person])
        path = self.path + person.id

        response = await make_get_request(path)
        assert response.body == person.dict(), \
            'Проверьте, что возвращенные данные совпадают.'

        await bulk(index=PERSON_INDEX, objects=[person], op_type='delete')

        response = await make_get_request(path)
        assert response.body == person.dict(), \
            'Проверьте, что после удаления из elastic, ' \
            'данные приходят из кэша.'

        await cache.flushall()
        response = await make_get_request(path)
        assert 'detail' in response.body
        assert (response.body['detail'] == 'персонаж не найден' or
                response.body['detail'] == 'Persons not found'), \
            'Проверьте, что данные очищаются из кэша.'

    @pytest.mark.asyncio
    async def test_08_person_films(self, make_get_request, bulk):
        films = FilmFactory.build_batch(10)
        person = PersonDetailsFactory(film_ids=[film.id for film in films])
        await bulk(index=FILM_INDEX, objects=films)
        await bulk(index=PERSON_INDEX, objects=[person])

        path = f"{self.path}{person.id}/films/"
        response = await make_get_request(path)
        assert response.status == 200, \
            'Проверьте, что при GET запросе возвращается статус 200'

        data = response.body
        assert FilmPagination(**data), \
            'Данные не соответствуют модели `FilmPagination`'

        assert data['count'] == len(films), \
            'Значение параметра `count` не верное'

        assert data['results'] == films, \
            'Данные не совпадают'
