# coding=utf-8
# coding=utf-8
from flask import Flask
from .utils.loading import load
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()


def create_app(config=None):
    config = config or {}
    app = Flask(__name__)

    db.init_app(app)
    ma.init_app(app)

    app.config.from_object('app.settings.default')

    load(app, '.', params=app.config.get('LOAD_PARAMS'))

    return app
