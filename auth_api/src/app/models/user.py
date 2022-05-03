import uuid
from datetime import date, datetime

import pyotp
from app import db
from app.db.cache import set_token
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jti)
from flask_security import UserMixin
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from .journal import Journal
from .mixins import BaseMixin
from .rbac import Role


class User(db.Model, BaseMixin, UserMixin):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                   unique=True, nullable=False)
    email = db.Column(db.String(200), index=True, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    is_superuser = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, default=True)
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.now)

    profile = db.relationship('Profile', back_populates='user', uselist=False)
    roles = db.relationship(Role, secondary='auth.roles_users',
                            backref=db.backref('users', lazy='dynamic'))
    events = db.relationship(Journal, backref='user')
    totp = db.relationship('TOTPDevice', back_populates='user', uselist=False)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == 'password':
                    self.set_password(value)
                else:
                    setattr(self, key, value)

    def __repr__(self):
        return f'<User {self.email} {self.id} {self.password}>'

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)

    def create(self, data):
        for field in ['email']:
            if field in data:
                setattr(self, field, data[field])
        if 'password' in data:
            self.set_password(data['password'])

    def encode_token_pair(self):
        refresh_token = create_refresh_token(identity=self)
        set_token(refresh_token)
        access_token = create_access_token(
            identity=self,
            additional_claims={
                'name': self.full_name,
                'rti': get_jti(refresh_token)
            }
        )
        token_pair = {
            'access_token': access_token,
            'refresh_token': refresh_token
        }
        return token_pair

    @property
    def full_name(self):
        profile = self.profile
        full_name = '%s %s' % (profile.first_name, profile.last_name)
        return full_name.strip().title()

    @property
    def age(self):
        if self.profile.birth_date:
            birth_date = self.profile.birth_date
            today = date.today()
            age = today.year - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
            return age
        return None

    def add_roles(self, role_ids):
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        for role in roles:
            if role not in self.roles:
                self.roles.append(role)
        db.session.commit()

    def remove_roles(self, role_ids):
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        for role in roles:
            if role in self.roles:
                self.roles.remove(role)
        db.session.commit()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()


class Profile(db.Model, BaseMixin):
    __tablename__ = 'profiles'
    __table_args__ = {'schema': 'auth'}

    id = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.users.id'),
                   primary_key=True, nullable=False)
    last_name = db.Column(db.String(100), default='')
    first_name = db.Column(db.String(100), default='')
    birth_date = db.Column(db.Date, default=None)
    phone = db.Column(db.String(12), default='')

    user = db.relationship(User, back_populates='profile')

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self):
        return f'<Profile {self.first_name} {self.last_name}>'


class TOTPDevice(db.Model, BaseMixin):
    __tablename__ = 'totp_device'
    __table_args__ = {'schema': 'auth'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                   unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.users.id'))
    confirmed = db.Column(db.Boolean, default=False)
    key = db.Column(db.String, nullable=False)
    digits = db.Column(db.Integer, nullable=False, default=6)
    interval = db.Column(db.Integer, nullable=False, default=30)

    user = db.relationship(User, back_populates='totp')

    def enabled(self):
        key = pyotp.random_base32()
        self.key = key
        self.save()
        totp = pyotp.TOTP(key)
        return totp.provisioning_uri(name=self.user.email,
                                     issuer_name='Movies')

    def verify(self, code):
        totp = pyotp.TOTP(self.key, digits=self.digits, interval=self.interval)
        return totp.verify(code)


@event.listens_for(User, 'after_insert')
def receive_after_insert(mapper, connection, user):
    @event.listens_for(db.session, 'after_flush', once=True)
    def receive_after_flush(session, context):
        session.add(Profile(id=user.id))
