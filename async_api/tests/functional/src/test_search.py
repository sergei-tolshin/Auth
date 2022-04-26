import factory
import pytest
from faker import Factory as FakerFactory
from functional.settings import config
from functional.testdata.films.factories import FilmFactory
from functional.testdata.films.models import FilmPagination
from functional.testdata.films.schema import SCHEMA as films_schema
from functional.testdata.persons.factories import PersonFactory
from functional.testdata.persons.models import PersonPagination
from functional.testdata.persons.schema import SCHEMA as persons_schema

PERSON_INDEX = config.ELASTIC_INDEX['persons']
FILM_INDEX = config.ELASTIC_INDEX['films']

fake = FakerFactory.create()


@pytest.fixture(scope='class')
async def persons_index(es_client):
    await es_client.indices.create(index=PERSON_INDEX, body=persons_schema)
    yield
    await es_client.indices.delete(index=PERSON_INDEX)


@pytest.fixture(scope='class')
async def films_index(es_client):
    await es_client.indices.create(index=FILM_INDEX, body=films_schema)
    yield
    await es_client.indices.delete(index=FILM_INDEX)


@pytest.mark.usefixtures('persons_index', 'films_index')
class TestSearchAPI:
    @pytest.fixture(autouse=True)
    async def clear_storage(self, es_client):
        query = {"query": {"match_all": {}}}
        await es_client.delete_by_query(index=PERSON_INDEX, body=query,
                                        refresh=True)
        await es_client.delete_by_query(index=FILM_INDEX, body=query,
                                        refresh=True)

    @pytest.fixture(autouse=True)
    async def clear_cache(self, cache):
        await cache.flushall()

    @pytest.mark.asyncio
    async def test_01_person_search(self, make_get_request, bulk):
        lazy_full_name = factory.LazyAttribute(
            lambda x: 'Uniquename ' + fake.name())
        persons = PersonFactory.build_batch(10, full_name=lazy_full_name)
        await bulk(index=PERSON_INDEX, objects=persons)
        persons = PersonFactory.build_batch(20)
        await bulk(index=PERSON_INDEX, objects=persons)

        path = '/api/v1/persons/search'

        response = await make_get_request(path)
        assert response.status == 422, \
            'Запрос без параметров возвращает статус 422'

        params = {'query': persons[3].full_name, }
        response = await make_get_request(path, params)
        data = response.body
        assert PersonPagination(**data), \
            'Данные не соответствуют модели'

        assert data['results'][0] == persons[3], \
            'Найденные данные не совпадают'

        params = {
            'query': 'Uniquename',
            'page[size]': 5
        }
        response = await make_get_request(path, params)
        data = response.body
        assert data['count'] == 10
        assert len(data['results']) == params['page[size]'], \
            'Количество результатов не совпадает с количеством на странице'

        params = {'query': 'UnknownPerson123'}
        response = await make_get_request(path, params)
        data = response.body
        assert len(data['results']) == 0, \
            'Значение параметра `results` не правильное'

    @pytest.mark.asyncio
    async def test_02_person_search_cache_update(self, make_get_request,
                                                 bulk, cache):
        persons = PersonFactory.build_batch(5)
        await bulk(index=PERSON_INDEX, objects=persons)

        path = '/api/v1/persons/search'
        params = {
            'query': persons[2].full_name,
            'page[number]': '1',
            'page[size]': '10'
        }
        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == persons[2].dict(), \
            'Проверьте, что возвращенные данные совпадают.'

        persons[2].full_name = 'updated name'
        await bulk(index=PERSON_INDEX, objects=persons)

        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] != persons[2].dict(), \
            'Проверьте, что данные в elastic и redis не совпадают.'

        await cache.flushall()
        params = {
            'query': persons[2].full_name,
            'page[number]': '1',
            'page[size]': '10'
        }
        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == persons[2].dict(), \
            'Проверьте, что после очистки кэша данные обновились.'

    @pytest.mark.asyncio
    async def test_03_person_search_cache_delete(self, bulk,
                                                 make_get_request, cache):
        persons = PersonFactory.build_batch(5)
        await bulk(index=PERSON_INDEX, objects=persons)
        path = '/api/v1/persons/search'
        params = {
            'query': persons[2].full_name,
            'page[number]': '1',
            'page[size]': '10'
        }

        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == persons[2].dict(), \
            'Проверьте, что возвращенные данные совпадают.'

        await bulk(index=PERSON_INDEX, objects=[persons[2]], op_type='delete')

        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == persons[2].dict(), \
            'Проверьте, что после удаления из elastic, ' \
            'данные приходят из кэша.'

        await cache.flushall()
        response = await make_get_request(path, params)
        assert len(response.body['results']) == 0, \
            'Проверьте, что данные очищаются из кэша.'

    @pytest.mark.asyncio
    async def test_04_films_search(self, make_get_request, bulk):
        films = FilmFactory.build_batch(10, title=factory.LazyAttribute(
            lambda x: 'Uniquetitle ' + fake.name()))
        await bulk(index=FILM_INDEX, objects=films)
        films = FilmFactory.build_batch(20)
        await bulk(index=FILM_INDEX, objects=films)

        path = '/api/v1/films/search'

        response = await make_get_request(path)
        assert response.status == 422, \
            'Запрос без параметров возвращает статус 422'

        params = {'query': films[3].title}
        response = await make_get_request(path, params)
        data = response.body
        assert FilmPagination(**data), \
            'Данные не соответствуют модели'

        assert data['results'][0] == films[3], \
            'Найденные данные не совпадают'

        params = {
            'query': 'Uniquetitle',
            'page[size]': 5
        }
        response = await make_get_request(path, params)
        data = response.body
        assert data['count'] == 10
        assert len(data['results']) == params['page[size]'], \
            'Количество результатов не совпадает с количеством на странице'

        params = {'query': 'UnknownFilm123'}
        response = await make_get_request(path, params)
        data = response.body
        assert len(data['results']) == 0, \
            'Значение параметра `results` не правильное, ' \
            'Должно быть 0 при отсетствии результатов'

    @pytest.mark.asyncio
    async def test_05_films_search_cache_update(self, make_get_request,
                                                bulk, cache):
        films = FilmFactory.build_batch(5)
        await bulk(index=FILM_INDEX, objects=films)

        path = '/api/v1/films/search'
        params = {
            'query': films[2].title,
            'page[number]': '1',
            'page[size]': '10'
        }
        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == films[2].dict(), \
            'Проверьте, что возвращенные данные совпадают.'

        films[2].title = 'updated title'
        await bulk(index=FILM_INDEX, objects=films)

        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] != films[2].dict(), \
            'Проверьте, что данные в elastic и redis не совпадают.'

        await cache.flushall()
        params = {
            'query': films[2].title,
            'page[number]': '1',
            'page[size]': '10'
        }
        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == films[2].dict(), \
            'Проверьте, что после очистки кэша данные обновились.'

    @pytest.mark.asyncio
    async def test_06_films_search_cache_delete(self, bulk,
                                                make_get_request, cache):
        films = FilmFactory.build_batch(5)
        await bulk(index=FILM_INDEX, objects=films)
        path = '/api/v1/films/search'
        params = {
            'query': films[2].title,
            'page[number]': '1',
            'page[size]': '10'
        }

        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == films[2].dict(), \
            'Проверьте, что возвращенные данные совпадают.'

        await bulk(index=FILM_INDEX, objects=[films[2]], op_type='delete')

        response = await make_get_request(path, params)
        data = response.body
        assert data['results'][0] == films[2].dict(), \
            'Проверьте, что после удаления из elastic, ' \
            'данные приходят из кэша.'

        await cache.flushall()
        response = await make_get_request(path, params)
        print(response.body)
        assert len(response.body['results']) == 0, \
            'Проверьте, что данные очищаются из кэша.'
