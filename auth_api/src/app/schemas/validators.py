import re

from app.models.rbac import Role
from app.models.user import User
from flask_babel import _
from marshmallow import ValidationError


def validate_email(email):
    user = User.find_by_email(email)
    if user is not None:
        raise ValidationError(_('The email address already exists.'))


def validate_role_name(name):
    role = Role.find_by_name(name)
    if role is not None:
        raise ValidationError(_('The role name already exists.'))


def validate_password(value):
    if len(value) < 8:
        raise ValidationError(_('Make sure your password is at lest 8 letters.'))
    # if re.search(r'[0-9]', value) is None:
    #     raise ValidationError('Make sure your password has a number in it.')
    # if re.search(r'[A-Z]', value) is None:
    #     raise ValidationError(
    #         'Make sure your password has a capital letter in it.')
    # if re.search(r'[`~\!@#\$%\^\&\*\(\)\-_\=\+\[\{\}\]\\\|;\:\'",<.>\/\?\€\£\¥\₹]+', value) is None:
    #     raise ValidationError(
    #         'Make sure your password has a special characters in it.')
    if re.search(r'[\s]+', value):
        raise ValidationError(_('The password must not contain spaces.'))
