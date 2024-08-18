import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.admin.admin import create_admin_app
from src.bot.bot import start_bot


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


@app.middleware("http")
async def force_https(request: Request, call_next):
    if request.url.scheme == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url)
    response = await call_next(request)
    return response
