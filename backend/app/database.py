import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Serverless hosts (Vercel) only allow writes under /tmp, and that data is ephemeral.
_default = "sqlite:////tmp/printqueue.db" if os.getenv("VERCEL") else "sqlite:///./printqueue.db"
DATABASE_URL = os.getenv("DATABASE_URL", _default)
_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
