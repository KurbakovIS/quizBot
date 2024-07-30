from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.admin.admin import create_admin_app

DATABASE_URL = "postgresql+asyncpg://postgres:qwerty@localhost:5432/tg_quiz_bot"

engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

app = FastAPI()

create_admin_app(app)


@app.get("/")
def read_root():
    return {"Hello": "World"}
