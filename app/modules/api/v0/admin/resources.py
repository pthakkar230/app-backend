from flask_login import current_user
from flask_restplus import Resource, Namespace

from app.utils.sessions import handle_rollback
from app.modules.api.v0.schemas import SeriesSchema

from ..models import User

ns = Namespace('admin', "Admin Access")


def loader(api, **params):
    """Load admin namespace to an Api"""
    api.add_namespace(ns)
    return ns


@ns.route('/users')
class Users(Resource):
    @ns.param('offset', 'query start index', type=int)
    @ns.param('limit', 'number of results', type=int)
    def get(self, offset, limit):
        return {'users': User.query.offset(offset).limit(limit)}

    def post(self):
        error = "Failed to create a new user."
        with handle_rollback(db.session, error):
            new_user = User(**args)
            db.session.add(new_user)
