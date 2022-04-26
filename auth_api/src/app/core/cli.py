import click
from app.models.user import User, Profile
from flask import Blueprint

create = Blueprint('create', __name__)


@create.cli.command('superuser')
@click.option('--email', prompt=True)
@click.password_option()
def create_superuser(email, password):
    # консольная команда для создания суперпользователя
    user = User(email=email, password=password, is_superuser=True)
    user = user.save()

    print(f'Superuser <{user.email}> created successfully')
