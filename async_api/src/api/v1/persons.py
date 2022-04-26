from core.fastapi_viewset.mixins import RelationViewMixin
from core.fastapi_viewset.router import MainRouter
from core.fastapi_viewset.viewsets import ViewSet
from services.films import Films
from services.persons import Persons

from .utils.persons import Filter

router = MainRouter()


@router.view(tags=['Люди'])
class PersonsViewSet(ViewSet, RelationViewMixin):
    model = Persons
    search_fields = ['full_name']
    filter_schema = Filter
    related_model = Films
    docum_api = {
        'retrieve': {
            'summary': 'Подробная информация о человеке',
            'description': 'Вывод подробной информации о человеке',
            'response_description': 'uuid, имя, роль, фильмы, фильмы по ролям',
        },
        'retrieve_list': {
            'summary': 'Список людей',
            'description': 'Постраничный список людей с фильтром по ролям',
            'response_description': 'uuid, имя, роли',
        },
        'retrieve_search': {
            'summary': 'Поиск по людям',
            'description': 'Постраничный вывод поиска по людям',
            'response_description': 'uuid, имя, роли, фильмы',
        },
        'retrieve_relation': {
            'summary': 'Фильмы с участием человека',
            'description': ('Постраничный вывод списка фильмов \
                            с участием человека'),
            'response_description': 'uuid, название, рейтинг',
        },
    }
