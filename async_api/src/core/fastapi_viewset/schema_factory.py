from typing import List

from pydantic.main import ModelMetaclass


class SchemaFactory:

    @classmethod
    def input_schema(cls, model):
        modul = __import__(f'models.{model.__name__.lower()}', fromlist=[
            f'{model.__name__.title()}ElasticModel'])
        return getattr(modul, f'{model.__name__.title()}ElasticModel')

    @classmethod
    def output_schema(cls, model):
        modul = __import__(f'models.{model.__name__.lower()}', fromlist=[
            f'{model.__name__.title()}ResponseModel'])
        return getattr(modul, f'{model.__name__.title()}ResponseModel')

    @classmethod
    def output_detail_schema(cls, model):
        modul = __import__(f'models.{model.__name__.lower()}', fromlist=[
            f'{model.__name__.title()}DetailsResponseModel'])
        return getattr(modul, f'{model.__name__.title()}DetailsResponseModel')

    @classmethod
    def list_schema(cls, base_schema, base_list_schema, schema_name=None):
        return ModelMetaclass(
            schema_name,
            (base_list_schema,),
            {'__annotations__': {'results': List[base_schema]}},
        )
