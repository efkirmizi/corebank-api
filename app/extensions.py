"""Flask extension singletons, initialized in the app factory."""
from flask_jwt_extended import JWTManager
from flask_smorest import Api

api = Api()
jwt = JWTManager()
