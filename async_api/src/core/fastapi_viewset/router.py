from fastapi import APIRouter

from .utils import camel_to_snake_case


class MainRouter(APIRouter):
    @classmethod
    def _build_single_obj_path(cls, base_path, name='id', annotation=str):
        return f'{base_path}{{{name}:{annotation.__name__}}}'

    def view(self, base_path: str = '', tags: list = None, **kwargs):
        def decorator(view):
            nonlocal base_path, tags
            if not base_path:
                tag = camel_to_snake_case(view.model.__name__)
                base_path = '/' + tag + '/'
                if tags is None:
                    tags = [tag]

            name = getattr(view, 'key_name', 'id')
            annotation = getattr(view, 'key_type', str)
            path = self._build_single_obj_path(base_path, name, annotation)

            if hasattr(view, 'retrieve_search'):
                docum_api = view.docum_api.get('retrieve_search') or {}
                method = self.get(
                    path=base_path + 'search',
                    response_model=view.list_schema,
                    tags=tags,
                    **kwargs,
                    **docum_api
                )
                method(view.retrieve_search)

            if hasattr(view, 'retrieve'):
                docum_api = view.docum_api.get('retrieve') or {}
                method = self.get(
                    path=path,
                    response_model=view.output_detail_schema,
                    tags=tags,
                    **kwargs,
                    **docum_api
                )
                method(view.retrieve)

            if hasattr(view, 'retrieve_list'):
                docum_api = view.docum_api.get('retrieve_list') or {}
                method = self.get(
                    path=base_path,
                    response_model=view.list_schema,
                    tags=tags,
                    **kwargs,
                    **docum_api)
                method(view.retrieve_list)

            if hasattr(view, 'retrieve_relation'):
                docum_api = view.docum_api.get('retrieve_relation') or {}
                related_model = view.related_model.__name__.lower()
                method = self.get(
                    path=path + '/' + related_model + '/',
                    response_model=view.list_relation_schema,
                    tags=tags,
                    **kwargs,
                    **docum_api)
                method(view.retrieve_relation)

        return decorator
