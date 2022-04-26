
from core import config
from db.manager import DataManager
from models.genres import GenresElasticModel

from .base import BaseService


class Genres(DataManager, BaseService):
    index = config.ELASTIC_INDEX['genres']
    model = GenresElasticModel
