from typing import List, Optional

from core import config


class RequestParams:
    async def get_query(self,
                        params: dict,
                        index: str,
                        search_fields: Optional[List] = None,
                        ) -> dict:
        # Парсит параметры и формирует запрос в elastic
        _index = params.get('_index')
        body = params.get('body')
        query = params.get('query')
        filter_genre = params.get('filter[genre]')
        filter_role = params.get('filter[role]')
        sort = params.get('sort')
        page_number = int(params.get('page[number]') or 1)
        page_size = int(params.get('page[size]') or config.PAGE_SIZE)

        if not _index:
            _index = index

        if not body:
            body: dict = {'query': {'match_all': {}}}

        if filter_genre:
            body = {
                'query': {
                    'nested': {
                        'path': 'genre',
                        'query': {
                            'bool': {
                                'must': [
                                    {'term': {'genre.id': filter_genre}},
                                ]
                            }
                        }
                    }
                }
            }

        if filter_role:
            body = {'query': {'term': {'roles': filter_role}}}

        if query:
            body: dict = {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fuzziness': 'auto',
                        'fields': search_fields
                    }
                }
            }

        sort_field = sort[0] if not isinstance(sort, str) and sort else sort
        if sort_field:
            order = 'desc' if sort_field.startswith('-') else 'asc'
            sort_field = f"{sort_field.removeprefix('-')}:{order}"

        query_params = {
            'index': _index,
            'body': body,
            'sort': sort_field,
            'size': page_size,
            'from_': (page_number - 1) * page_size
        }

        query_params = {key: value for key, value in query_params.items()
                        if value is not None}

        return query_params
