from core import config
from db.manager import DataManager
from models.films import FilmsElasticModel

from .base import BaseService


class Films(DataManager, BaseService):
    index = config.ELASTIC_INDEX['films']
    model = FilmsElasticModel
    search_fields = ['title', 'description']
