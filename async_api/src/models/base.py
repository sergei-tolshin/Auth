import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode,
    # поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class OrjsonMixin(BaseModel):

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class UUIDMixin(BaseModel):
    id: str


class ESBaseModel(OrjsonMixin, UUIDMixin):
    """Базовая модель для работы с ES"""
