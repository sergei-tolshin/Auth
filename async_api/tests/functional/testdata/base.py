import orjson
from pydantic import BaseModel
from typing import Optional


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode,
    # поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class OrjsonMixin(BaseModel):

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class PaginationMixin(BaseModel):
    """Модель ответа API с пагинацией"""
    count: int
    total_pages: int
    next: Optional[str] = None
    previous: Optional[str] = None
