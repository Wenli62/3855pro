from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml
import os

user = os.getenv("MYSQL_USER")

with open('/config/storage_config.prod.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

user = os.getenv("MYSQL_USER")
password = os.getenv("MYSQL_ROOT_PASSWORD")
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = os.getenv("MYSQL_DATABASE")

engine = create_engine(f"mysql://{user}:{password}@{hostname}:{port}/{db}")

def make_session():
    return sessionmaker(bind=engine)()