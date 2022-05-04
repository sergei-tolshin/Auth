import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from concurrent import futures

import grpc
import messages.user_pb2_grpc as user_service
from services.user import UserService
from app import create_app


def grpc_server():
    app = create_app()
    config = app.config
    port = config.get('GRPC_PORT', 50051)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    user_serve = UserService(app)
    user_service.add_UserServicer_to_server(user_serve, server)

    server.add_insecure_port(f'[::]:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    grpc_server()
