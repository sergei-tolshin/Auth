from core.fastapi_viewset.router import MainRouter
from core.fastapi_viewset.viewsets import ReadOnlyViewSet
from services.genres import Genres

from .utils.genres import Sort

router = MainRouter()


@router.view(tags=['Жанры'])
class GenresViewSet(ReadOnlyViewSet):
    model = Genres
    sort_schema = Sort
    docum_api = {
        'retrieve': {
            'summary': 'Подробная информация о жанре',
            'description': 'Вывод подробной информации о жанре',
            'response_description': 'uuid, название, описание',
        },
        'retrieve_list': {
            'summary': 'Список жанров',
            'description': ('Список жанров с пагинацией \
                            и сортировкой по названию'),
            'response_description': 'uuid, название',
        },
    }
