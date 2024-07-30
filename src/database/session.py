from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import mapper_registry

DATABASE_URL = "postgresql://postgres:qwerty@localhost/tg_quiz_bot"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


mapper_registry.metadata.create_all(engine)
