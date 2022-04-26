import uuid

from app import db
from flask_security import RoleMixin
from sqlalchemy.dialects.postgresql import UUID

from .mixins import BaseMixin


class RolesUsers(db.Model, BaseMixin):
    __tablename__ = 'roles_users'
    __table_args__ = {'schema': 'auth'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                   unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.users.id'))
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.roles.id'))


class Role(db.Model, BaseMixin, RoleMixin):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'auth'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                   unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), default='')

    def __repr__(self):
        return f'<Role {self.name}>'

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def add_to_users(self, users):
        for user in users:
            if user not in self.users:
                self.users.append(user)
        db.session.commit()

    def remove_from_users(self, users):
        for user in users:
            if user in self.users:
                self.users.remove(user)
        db.session.commit()
