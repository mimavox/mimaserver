from sqlmodel import create_engine as sqlmodel_create_engine, SQLModel
from database import models # Import SQL models

# Creates connection with PostgreSQL backend.
def create_engine(url):
    return sqlmodel_create_engine(url)

# The SQL models are used to create db-tables
def clear_db_and_tables(engine):
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
