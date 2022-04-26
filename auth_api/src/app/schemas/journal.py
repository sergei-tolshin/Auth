from app import ma
from app.models.journal import Journal
from marshmallow import fields


class JournalSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Journal
        fields = ('id', 'action', 'ip', 'user_agent', 'created',)
        ordered = True
        load_instance = True

    action = fields.Method('get_action_value')

    def get_action_value(self, obj):
        return str(obj.action)


class SessionSchema(ma.Schema):
    class Meta:
        ordered = True

    id = fields.Str()
    ip = fields.Str()
    user_agent = fields.Str()
    last_activity = fields.DateTime()
