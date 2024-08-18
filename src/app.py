import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.admin.admin import create_admin_app
from src.bot.bot import start_bot
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск бота при старте приложения
    bot_task = asyncio.create_task(start_bot())
    yield
    # Остановка бота при завершении приложения
    bot_task.cancel()
    try:
        await bot_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

create_admin_app(app)

app.mount("/static", StaticFiles(packages=['sqladmin']), name="static")