import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Store DB in local AppData — NOT in OneDrive which causes SQLite lock conflicts
_APP_DATA = os.path.join(os.path.expanduser("~"), "AppData", "Local", "TransactIQ")
os.makedirs(_APP_DATA, exist_ok=True)

_DB_PATH = os.path.join(_APP_DATA, "transactiq.db").replace("\\", "/")
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
