import grpc
import messages.user_pb2 as user_messages
import messages.user_pb2_grpc as user_service
from app.models.user import User


class UserService(user_service.UserServicer):
    def __init__(self, app):
        self.app = app

    def GetInfo(self, request, context):
        if request.id:
            with self.app.app_context():
                user = User().find_by_id(request.id)
                if user:
                    if not user.active:
                        msg = 'User not active'
                        context.set_details(msg)
                        context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                        return user_messages.UserInfoReply()

                    roles = [role.name for role in user.roles] or []
                    if user.is_superuser:
                        roles.append('superuser')
                    roles = ','.join(roles)
                    return user_messages.UserInfoReply(
                        id=str(user.id),
                        name=user.full_name,
                        email=user.email,
                        age=user.age,
                        roles=roles
                    )
                msg = 'User not found'
                context.set_details(msg)
                context.set_code(grpc.StatusCode.NOT_FOUND)
                return user_messages.UserInfoReply()
        msg = 'Must pass UUID'
        context.set_details(msg)
        context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
        return user_messages.UserInfoReply()
