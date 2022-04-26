import factory
from functional.testdata.genres.models import GenreDetailsModel, GenreModel


class GenreFactory(factory.Factory):

    class Meta:
        model = GenreModel

    id = factory.Faker('uuid4')
    name = factory.Faker('word')


class GenreDetailFactory(GenreFactory):

    class Meta:
        model = GenreDetailsModel

    description = factory.Faker('text', max_nb_chars=100)
