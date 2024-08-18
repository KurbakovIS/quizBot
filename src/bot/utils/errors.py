from aiogram import types
from loguru import logger


async def handle_error(message: types.Message, error_message: str, exception: Exception):
    logger.error(f"{error_message}: {exception}")
    await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


async def handle_error_answer(message: types.Message, error_msg: str):
    logger.error(error_msg)
    await message.answer("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.")
