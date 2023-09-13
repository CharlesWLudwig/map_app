from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .forms import LoginForm
from flask_login import LoginManager
from .config import ConfigClass

app = Flask(__name__)

app.config.from_object(ConfigClass)

app.config['JSON_SORT_KEYS'] = False
app.config["DEBUG"] = True
app.config["APPLICATION_ROOT"] = "/"

login = LoginManager(app)
login.login_view = 'login'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app import routes, forms, models 
from .models import User, Events, Post

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Post': Post,
        'Events': Events
    }