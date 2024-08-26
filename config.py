import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv('MYSQL_CONNSTRING', 'mysql+pymysql://user:password@localhost/dbname')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
