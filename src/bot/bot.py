import asyncio
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import router

API_TOKEN = '6939810787:AAFU363xcu1aVMUlbVcLMH_Awidr3R9RdR8'

logger.add("bot.log", rotation="10 MB")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

dp.include_router(router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Starting bot")
    asyncio.run(main())
