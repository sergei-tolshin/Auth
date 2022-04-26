from app import ma
from app.models.rbac import Role
from app.models.user import User
from flask_babel import _
from marshmallow import ValidationError, validates


class RoleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Role
        fields = ('id', 'name', 'description',)
        ordered = True

    @validates('name')
    def validate_name(self, name, load_only=True):
        role = Role.find_by_name(name)
        if role is not None:
            raise ValidationError(_('The role name already exists.'))


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'email',)
        ordered = True
        load_instance = True
