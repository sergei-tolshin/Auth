import random

import factory
from faker import Factory as FakerFactory
from functional.testdata.persons import models

fake = FakerFactory.create()
film_ids_list = [fake.uuid4() for i in range(random.randint(1, 10))]


class PersonFactory(factory.Factory):
    class Meta:
        model = models.PersonModel

    id = factory.Faker('uuid4')
    full_name = factory.Faker('name')
    roles = factory.LazyAttribute(lambda x: random.sample(
        ['actor', 'director', 'writer'], k=random.randint(1, 3)))
    film_ids = factory.LazyAttribute(
        lambda x: [fake.uuid4() for i in range(random.randint(1, 10))])


class PersonDetailsFactory(factory.Factory):
    class Meta:
        model = models.PersonDetailsModel

    id = factory.Faker('uuid4')
    full_name = factory.Faker('name')
    roles = random.sample(['actor', 'director', 'writer'],
                          k=random.randint(1, 3))
    actor_film_ids = []
    director_film_ids = []
    writer_film_ids = []
    if 'actor' in roles:
        actor_film_ids = [fake.uuid4() for i in range(random.randint(1, 3))]
    if 'director' in roles:
        director_film_ids = [fake.uuid4() for i in range(random.randint(1, 3))]
    if 'writer' in roles:
        writer_film_ids = [fake.uuid4() for i in range(random.randint(1, 3))]
    film_ids = actor_film_ids + director_film_ids + writer_film_ids
