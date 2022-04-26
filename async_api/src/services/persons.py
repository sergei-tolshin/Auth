from core import config
from db.manager import DataManager
from models.persons import PersonsElasticModel

from .base import BaseService


class Persons(DataManager, BaseService):
    index = config.ELASTIC_INDEX['persons']
    model = PersonsElasticModel
    search_fields = ['full_name']
