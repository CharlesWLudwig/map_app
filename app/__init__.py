from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .forms import LoginForm
from flask_login import LoginManager
from flask_babel import Babel
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
babel = Babel(app)

from app import routes, forms, models 
from .models import User, Events

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User,
        'Events': Events
    }

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])