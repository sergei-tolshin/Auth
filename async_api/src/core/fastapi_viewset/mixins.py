import math

from core.utils.translation import gettext_lazy as _
from fastapi import HTTPException, status

from .dynamic_method import MethodFactory
from .schema_factory import SchemaFactory
from .schemas import Pagination
from .utils import get_object_or_404, get_page_url, is_method_overloaded


class BaseMixin:
    input_schema = None
    output_schema = None
    output_detail_schema = None
    docum_api = {}


class ViewSetMeta(type):

    def __new__(mcs, name, bases, attrs):
        model = attrs.get('model')
        related_model = attrs.get('related_model')
        if model is not None:
            attrs['input_schema'] = attrs.get(
                'input_schema',) or SchemaFactory.input_schema(model)
            attrs['output_schema'] = attrs.get(
                'output_schema') or SchemaFactory.output_schema(model)
            attrs['output_detail_schema'] = attrs.get(
                'output_detail_schema') or \
                SchemaFactory.output_detail_schema(model)
            if related_model is not None:
                attrs['output_relation_schema'] = attrs.get(
                    'output_relation_schema') or \
                    SchemaFactory.output_schema(related_model)

        return super().__new__(mcs, name, bases, attrs)


class BaseViewMixin(BaseMixin, metaclass=ViewSetMeta):
    model = None

    @classmethod
    async def get_query(cls, params):
        query = await cls.model.get_query(params)
        return await cls.model.search(**query)

    @classmethod
    async def count(cls, query):
        return int(query.get('hits').get('total').get('value', 0))

    @classmethod
    async def get_pages(cls, request, count, num_results,
                        page_number, page_size):
        total_pages, next_page, previous_page = None, None, None
        if page_number > 1:
            previous_page = page_number - 1
        previous_items = (page_number - 1) * page_size
        if previous_items + num_results < count:
            next_page = page_number + 1
        total_pages: int = int(math.ceil(count / float(page_size)))
        if count > 0 and page_number > total_pages:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=_('Invalid page'))
        if count == 0 and page_number > 1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=_('Invalid page'))

        next_page_url = await get_page_url(request, next_page)
        previous_page_url = await get_page_url(request, previous_page)

        return total_pages, next_page_url, previous_page_url

    @classmethod
    def prepare_response(cls, count, total, next, previous, data):
        data = {
            'count': count,
            'total_pages': total,
            'next': next,
            'previous': previous,
            'results': data,
        }
        return data


class SingleObjectMixin:
    key_name = 'id'
    key_type = str
    retrieve_function = get_object_or_404


class RetrieveViewMixin(SingleObjectMixin, BaseViewMixin):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not is_method_overloaded(cls, 'retrieve'):
            cls.retrieve = classmethod(
                MethodFactory.make_retrieve(
                    cls.key_name,
                    cls.key_type,
                ),
            )


class BaseListViewMixin():
    base_list_schema = Pagination
    list_schema = None
    filter_schema = None
    sort_schema = None
    model = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        if model is not None:
            if cls.list_schema is None:
                cls.list_schema = SchemaFactory.list_schema(
                    cls.output_schema,
                    cls.base_list_schema,
                    f'{model.__name__.title()}ListSchema',
                )
            if cls.filter_schema is None:
                cls.filter_schema = object
            if cls.sort_schema is None:
                cls.sort_schema = object
            if not is_method_overloaded(cls, 'retrieve_list'):
                cls.retrieve_list = classmethod(
                    MethodFactory.make_retrieve_list(
                        cls.filter_schema,
                        cls.sort_schema
                    ),
                )


class SearchViewMixin():

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        model = getattr(cls, 'model', None)
        if model is not None:
            if not is_method_overloaded(cls, 'retrieve_search'):
                cls.retrieve_search = classmethod(
                    MethodFactory.make_retrieve_search(),
                )


class ListViewMixin(BaseViewMixin, BaseListViewMixin):
    pass


class RelationViewMixin(SingleObjectMixin, BaseViewMixin):
    list_relation_schema = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        related_model = getattr(cls, 'related_model', None)
        if cls.list_relation_schema is None:
            cls.list_relation_schema = SchemaFactory.list_schema(
                cls.output_relation_schema,
                cls.base_list_schema,
                f'{related_model.__name__.title()}ListRelationSchema',
            )
        if not is_method_overloaded(cls, 'retrieve_relation'):
            cls.retrieve_relation = classmethod(
                MethodFactory.make_retrieve_relation(
                    cls.key_name,
                    cls.key_type,
                    cls.related_model.__name__.lower()
                ),
            )
