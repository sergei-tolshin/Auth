from core.fastapi_viewset.router import MainRouter
from core.fastapi_viewset.viewsets import ViewSet
from services.films import Films

from .utils.films import Filter, Sort

router = MainRouter()


@router.view(tags=['Фильмы'])
class FilmsViewSet(ViewSet):
    model = Films
    filter_schema = Filter
    sort_schema = Sort
    docum_api = {
        'retrieve': {
            'summary': 'Подробная информация о фильме',
            'description': 'Вывод подробной информации о фильме',
            'response_description': ('uuid, название, описание, рейтинг, \
                                     актеры, режиссеры, сценаристы'),
        },
        'retrieve_list': {
            'summary': 'Список фильмов',
            'description': ('Список фильмов с пагинацией, \
                фильтрацией по жанрам и сортировкой по рейтингу'),
            'response_description': 'uuid, название, рейтинг',
        },
        'retrieve_search': {
            'summary': 'Поиск по фильмам',
            'description': 'Поиск по фильмам с пагинацией',
            'response_description': 'uuid, имя, роли, фильмы',
        },
    }
