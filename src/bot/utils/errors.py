from aiogram import types
from loguru import logger


async def handle_error(message: types.Message, error_message: str, exception: Exception):
    logger.error(f"{error_message}: {exception}")
    await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
