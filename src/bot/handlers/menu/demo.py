from aiogram import types
from loguru import logger

from src.bot.handlers.menu.get_main_menu import get_main_menu


async def handle_demo(message: types.Message):
    try:
        await message.answer(
            "Чтобы записаться на демо, пожалуйста, заполните форму по следующей ссылке: [ссылка на форму]")
    except Exception as e:
        logger.error(f"Error in handle_demo: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
