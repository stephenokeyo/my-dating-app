from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Association table for the many-to-many relationship of "Likes"
likes = db.Table('likes',
    db.Column('liker_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('liked_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.png')
    bio = db.Column(db.Text, nullable=True)
    gender = db.Column(db.String(10))
    interest = db.Column(db.String(10))
    interests_list = db.Column(db.String(500)) # e.g., "coding,music,travel"

    # Relationship for likes
    following = db.relationship(
        'User',
        secondary=likes,
        primaryjoin=(likes.c.liker_id == id),
        secondaryjoin=(likes.c.liked_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='select',
    )

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, nullable=False, default=False)