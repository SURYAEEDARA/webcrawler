from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.engine import Engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine: Engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency to get database session"""
    with Session(engine) as session:
        yield session