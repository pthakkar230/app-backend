from flask import Blueprint
from flask_restplus import Api, Namespace

from app.modules.api import api_blueprint
from app.utils import match_specs
from app.utils.loading import load

__version__ = "0.1.2"

api, bp = api_blueprint('api',
                        title="3Blades API",
                        version=__version__,
                        prefix="/" + __version__,
                        )


def loader(app, **params):
    namespaces = load(api, '.', params=params)
    app.register_blueprint(bp)
    return namespaces
