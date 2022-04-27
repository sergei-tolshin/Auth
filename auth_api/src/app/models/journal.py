import enum
import uuid
from datetime import datetime

from app import db
from flask_babel import _
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from user_agents import parse

from .mixins import BaseMixin


def create_partition(target, connection, **kw) -> None:
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "journal_in_smart" PARTITION OF "journal" FOR VALUES IN ('smart')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "journal_in_mobile" PARTITION OF "journal" FOR VALUES IN ('mobile')"""
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS "journal_in_web" PARTITION OF "journal" FOR VALUES IN ('web')"""
    )


class Action(enum.Enum):
    login = _('Login')
    logout = _('Logout')
    change_email = _('Change email')
    change_password = _('Change password')
    password_recovery = _('Password recovery')

    def __str__(self):
        return self.value


class Journal(db.Model, BaseMixin):
    __tablename__ = 'journal'
    __table_args__ = (
        UniqueConstraint('id', '_device_type'),
        {
            'schema': 'auth',
            'postgresql_partition_by': 'LIST (_device_type)',
            'listeners': [('after_create', create_partition)],
        }
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   default=uuid.uuid4, nullable=False)
    user_id = db.Column(UUID(as_uuid=True),
                        db.ForeignKey('auth.users.id'), nullable=False)
    action = db.Column(ENUM(Action), nullable=False)
    ip = db.Column(db.String(20))
    user_agent = db.Column(db.Text, nullable=True, default='')
    _device_type = db.Column(db.Text, nullable=False, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, action, request):
        self.action = action
        self.ip = request.environ.get(
            'HTTP_X_FORWARDED_FOR', request.remote_addr)
        self.user_agent = request.user_agent.string
        self.device_type = request.user_agent.string

    def __repr__(self):
        return f'<Event {self.action}::{self.user_id}>'

    @classmethod
    def get_by_user(cls, user):
        return cls.query.filter_by(user_id=user) \
            .order_by(cls.created.desc()).all()

    @hybrid_property
    def device_type(self):
        return self._device_type

    @device_type.setter
    def device_type(self, user_agent):
        ua = parse(user_agent)
        if ua.is_mobile or ua.is_tablet:
            self._device_type = 'mobile'
        elif (
            not ua.is_pc and
            'smart' in str(ua.device.model).lower() or
            'smart-tv' in user_agent.lower() or
            'smarttv' in user_agent.lower()
        ):
            self._device_type = 'smart'
        else:
            self._device_type = 'web'
