from flask import Blueprint
from flask_restplus import Api

from app.utils import match_specs
from app.utils.loading import load, frame_globals


def loader(app, **params):
    """Returns a Blueprint with loaded api"""
    specs = params.get('api_specs')
    if specs:
        def key(m):
            try:
                v = m.__version__
            except:
                raise AttributeError("Api modules require a '__version__' attribute")
            else:
                return match_specs(v, specs)
    else:
        key = None
    return load(app, '.', params=params, key=key)


def api_blueprint(name, *args, **kwargs):
    bp = Blueprint(name, frame_globals(1)['__name__'], url_prefix='/api',
                   *kwargs.pop('bp_args', ()), **kwargs.pop('bp_kwargs', {}))
    api = Api(bp, *args, **kwargs)
    return api, bp
