import os
from dotenv import load_dotenv
import json

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv('MYSQL_CONNSTRING', 'mysql+pymysql://user:password@localhost/dbname')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    CONFIG_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    with open(CONFIG_JSON_PATH, 'r') as config_file:
        CONFIG_JSON = json.load(config_file)
