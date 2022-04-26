import random

import factory

from factory import fuzzy
from functional.testdata.films import models
from functional.testdata.genres.factory import GenreFactory

available_genres = [GenreFactory() for _ in range(10)]


class FilmFactory(factory.Factory):
    class Meta:
        model = models.FilmModel

    id = factory.Faker('uuid4')
    title = factory.Faker('sentence', nb_words=5)
    imdb_rating = fuzzy.FuzzyDecimal(low=0, high=10, precision=1)


class FilmDetailFactory(FilmFactory):
    class Meta:
        model = models.FilmDetailsModel

    film_type = factory.fuzzy.FuzzyChoice(['movie', 'tv-show'])
    description = factory.Faker('paragraph', nb_sentences=3)
    genre = factory.LazyAttribute(
        lambda x: random.sample(available_genres, k=random.randint(1, 5))
    )
