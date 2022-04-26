from flask import Blueprint

from .account.urls import router as account_router
from .auth.urls import router as auth_router
from .rbac.urls import router as rbac_router

v1 = Blueprint('v1', __name__, url_prefix='/v1')

v1.register_blueprint(auth_router)
v1.register_blueprint(account_router)
v1.register_blueprint(rbac_router)
