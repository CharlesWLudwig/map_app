from configparser import ConfigParser
import os

BASEDIR = os.path.abspath(os.path.dirname(__file__))

class ConfigClass(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'there-is-no-key'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASEDIR, 'trafficapp.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

# This is for online db (if you have a file for the connection string - .ini)
def config_db(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        pass
    
    return db