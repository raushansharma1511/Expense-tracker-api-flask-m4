from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
from flask_mail import Mail
import redis
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import g


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
ma = Marshmallow()
mail = Mail()

redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    decode_responses=True,
)


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["5 per day"],
    storage_uri="redis://localhost:6379/0",
)


def init_limiter(app):
    limiter.init_app(app)
