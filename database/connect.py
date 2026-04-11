from sqlmodel import create_engine as sqlmodel_create_engine, SQLModel
from database import models

def create_engine(url):
    return sqlmodel_create_engine(url)

def create_db_and_tables(engine):
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    