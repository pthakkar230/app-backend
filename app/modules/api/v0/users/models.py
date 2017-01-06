from app import db
from flask_security import UserMixin

class User(db.Model, UserMixin):
    """
    User database model.
    """
    __tablename__ = 'user'
    __table_args__ = {'useexisting': True} 

    user_id = db.Column(
        db.Integer,
        primary_key=True,
    )
    username = db.Column(
        db.String(120),
        nullable=False,
        unique=True,
        index=True,
    )
    first_name = db.Column(
        db.String(30),
        nullable=False,
    )
    last_name = db.Column(
        db.String(30),
    )
    email = db.Column(
        db.String(120),
        nullable=False,
        unique=True,
        index=True,
    )
    avatar_url = db.Column(
        db.String(100),
        nullable=True,
    )
    bio = db.Column(
        db.String(400),
        nullable=True,
    )
    location = db.Column(
        db.String(120),
        nullable=True,
    )
    company = db.Column(
        db.String(255),
        nullable=True,
    )
    timezone = db.Column(
        'Timezone',
        db.String(20),
        nullable=True
    )
    active = db.Column(
        db.Boolean,
        default=True,
    )
    confirmed_at = db.Column(
        db.DateTime,
    )
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now(),
    )
    updated = db.Column(
        'last_updated',
        db.DateTime,
        onupdate=db.func.now(),
    )
