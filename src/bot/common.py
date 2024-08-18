import logging
from aiogram import types

async def handle_common_error(message: types.Message, context: str, exception: Exception):
    logging.error(f"{context}: {exception}")
    if message:
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
