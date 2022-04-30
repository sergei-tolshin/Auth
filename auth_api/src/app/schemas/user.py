import phonenumbers
from app import ma
from app.models.user import Profile, User
from marshmallow import fields

from .validators import validate_email, validate_password


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'birth_date',
                  'phone', 'roles', 'date_joined',)
        ordered = True
        load_instance = True

    full_name = fields.Method('get_full_name')
    birth_date = fields.Method('get_birth_date')
    phone = fields.Method('get_phone')
    roles = fields.Method('get_roles')

    def get_full_name(self, obj):
        profile = obj.profile
        full_name = '%s %s' % (profile.first_name.title(),
                               profile.last_name.title())
        return full_name.strip().title()

    def get_birth_date(self, obj):
        if obj.profile.birth_date:
            birth_date = obj.profile.birth_date.strftime('%d.%m.%Y')
            return birth_date

    def get_phone(self, obj):
        if obj.profile.phone:
            phone_number = phonenumbers.parse(obj.profile.phone, None)
            phone = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164)
            return phone.strip()

    def get_roles(self, obj):
        return [role.name for role in obj.roles]


class ProfileSchema(ma.Schema):
    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'birth_date', 'phone')
        ordered = True

    phone = fields.Method('get_phone', deserialize='load_phone')

    def get_phone(self, obj):
        return obj.income - obj.debt

    def load_phone(self, value):
        if value:
            phone_number = phonenumbers.parse(value, 'RU')
            phone = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164)
            return phone.strip()


class LoginSchema(ma.Schema):
    email = fields.Email()
    password = fields.Str(load_only=True)


class RegisterSchema(ma.Schema):
    email = fields.Email(validate=validate_email)
    password = fields.Str(validate=validate_password, load_only=True)


class ChangePasswordSchema(ma.Schema):
    current_password = fields.Str(load_only=True)
    new_password = fields.Str(validate=validate_password, load_only=True)
    logout_everywhere = fields.Boolean(default=True)


class ChangeEmailSchema(ma.Schema):
    current_email = fields.Email(load_only=True)
    new_email = fields.Email(validate=validate_email, load_only=True)
    logout_everywhere = fields.Boolean(default=True)


class CodeSchema(ma.Schema):
    code = fields.Int()
