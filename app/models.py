from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    events = db.relationship('Events', backref='user_events', lazy = 'dynamic') 

    posts = db.relationship('Post', backref='user_posts', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'
           
class Events(db.Model):

    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    event_name = db.Column(db.String(64), nullable = False)
    event_city = db.Column(db.String(64), nullable = False)
    event_state = db.Column(db.String(64), nullable = False)
    event_country = db.Column(db.String(64), nullable = False)
    event_type = db.Column(db.String(64), nullable = False)
    event_latitude = db.Column(db.String(64), nullable = False)
    event_longitude = db.Column(db.String(64), nullable = False)
    event_duration = db.Column(db.String(64), nullable = False)
#    date_created =db.Column(String("Date Created"), default = datetime.utcnow)

    customer = db.Column(db.Integer(), db.ForeignKey('users.id'))
    
    def _repr_(self):
        return f'<Events {self.id}>'
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    body = db.Column(db.String(100))

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<Post {self.body}>'   
