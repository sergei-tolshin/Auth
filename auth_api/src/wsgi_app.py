from gevent import monkey
monkey.patch_all()

from app import create_app
from app.core.config import ProductionConfig

app = create_app(ProductionConfig)
