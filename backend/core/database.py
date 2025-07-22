from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from models.base import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables (for dev/demo; use Alembic for production)
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
