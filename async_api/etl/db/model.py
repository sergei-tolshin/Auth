from utils.mixins import ModifiedMixin, UUIDMixin

from .manager import BaseManager


class MetaModel(type):
    manager_class = BaseManager

    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @ property
    def objects(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    table_name = ''
    object_model = None
    instance_model = None
    relations = None

    def __init__(self, **row_data):
        for field_name, value in row_data.items():
            setattr(self, field_name, value)


class PostgresBaseModel(UUIDMixin, ModifiedMixin):
    """Базовая модель"""
