from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(64), index=True, unique=True)

    email = db.Column(db.String(120), index=True, unique=True)

    password_hash = db.Column(db.String(128))

    events = db.relationship('Event', backref='scheduler', lazy='dynamic')
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    event_name = db.Column(db.String(64), nullable = False)
    event_street = db.Column(db.String(64), nullable = False)
    event_city = db.Column(db.String(64), nullable = False)
    event_state = db.Column(db.String(64), nullable = False)
    event_country = db.Column(db.String(64), nullable = False)
    event_postalcode = db.Column(db.String(64), nullable = False)
    event_type = db.Column(db.String(64), nullable = False)
    event_latitude = db.Column(db.String(64), nullable = True)
    event_longitude = db.Column(db.String(64), nullable = True)
    event_time = db.Column(db.String(64), nullable = True)
    event_date = db.Column(db.String(64), nullable = True)
    event_duration = db.Column(db.String(64), nullable = False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Event {self.id}>'