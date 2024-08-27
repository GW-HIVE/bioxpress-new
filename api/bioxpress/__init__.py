from flask import Flask
from bioxpress.db import db
from bioxpress.routes.api import api_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object("bioxpress.config.Config")
    db.init_app(app)
    app.register_blueprint(api_bp)
    return app
