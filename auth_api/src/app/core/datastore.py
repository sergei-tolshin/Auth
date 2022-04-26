from app import db
from app.models.rbac import Role
from app.models.user import User
from flask_security import SQLAlchemyUserDatastore

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
