import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

from config import settings

engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False},
    poolclass=NullPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    __table_args__ = {"extend_existing": True}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
