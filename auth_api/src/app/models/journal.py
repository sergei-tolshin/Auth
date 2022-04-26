import enum
import uuid
from datetime import datetime

from app import db
from flask_babel import _
from sqlalchemy.dialects.postgresql import ENUM, UUID

from .mixins import BaseMixin


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
    __table_args__ = {'schema': 'auth'}

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                   unique=True, nullable=False)
    user_id = db.Column(UUID(as_uuid=True),
                        db.ForeignKey('auth.users.id'), nullable=False)
    action = db.Column(ENUM(Action), nullable=False)
    ip = db.Column(db.String(20))
    user_agent = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, action, request):
        self.action = action
        self.ip = request.environ.get(
            'HTTP_X_FORWARDED_FOR', request.remote_addr)
        self.user_agent = request.user_agent.string

    def __repr__(self):
        return f'<Event {self.action}::{self.ip}>'

    @classmethod
    def get_by_user(cls, user):
        return cls.query.filter_by(user_id=user) \
            .order_by(cls.created.desc()).all()
