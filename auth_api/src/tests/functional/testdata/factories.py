import factory
from app import db
from app.models.rbac import Role
from app.models.user import User
from app.schemas.user import (ChangeEmailSchema, ChangePasswordSchema,
                              ProfileSchema, RegisterSchema)

from .mixins import ObjFactoryMixin


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session

    email = factory.Faker('email')
    password = 'password'


class RegisterUserFactory(ObjFactoryMixin, factory.Factory):
    class Meta:
        model = RegisterSchema

    email = factory.Faker('email')
    password = factory.Faker('password', length=8)


class ProfileFactory(ObjFactoryMixin, factory.Factory):
    class Meta:
        model = ProfileSchema

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    birth_date = factory.Faker('date')
    phone = factory.Faker('phone_number', locale='ru_RU')


class ChangePasswordFactory(ObjFactoryMixin, factory.Factory):
    class Meta:
        model = ChangePasswordSchema

    current_password = factory.Faker('password', length=8)
    new_password = factory.Faker('password', length=8)
    logout_everywhere = True


class ChangeEmailFactory(ObjFactoryMixin, factory.Factory):
    class Meta:
        model = ChangeEmailSchema

    current_email = factory.Faker('email')
    new_email = factory.Faker('email')
    logout_everywhere = True


class RoleFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Role
        sqlalchemy_session = db.session

    name = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=10)
