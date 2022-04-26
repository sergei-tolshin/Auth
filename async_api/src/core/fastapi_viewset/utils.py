import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from core.utils.translation import gettext_lazy as _
from fastapi import HTTPException, status


def is_method_overloaded(cls, method_name) -> bool:
    method = getattr(cls, method_name, False)
    return method and method != getattr(super(cls, cls), method_name, None)


def camel_to_snake_case(words: str):
    return re.sub('([A-Z][a-z]+)', r'\1_', words).rstrip('_').lower()


def create_meta_class(model, **kwargs):
    return type('Meta', (), {'model': model, **kwargs})


async def get_object_or_404(model, id):
    obj = await model.get(id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=_(f'{model.__name__} not found'))
    return obj


async def get_page_url(request, page):
    if page is None:
        return None

    url = str(request.url)
    url_parts = list(urlparse(url))
    params = {'page[number]': page}
    query = dict(parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query, safe='[]')
    return urlunparse(url_parts)
