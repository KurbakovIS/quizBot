from aiogram import types
from loguru import logger

from src.bot.handlers.menu.get_main_menu import get_main_menu


async def handle_shop(message: types.Message):
    try:
        await message.answer(
            "Добро пожаловать в наш магазин мерча! Пожалуйста, посетите следующую ссылку для покупок: [ссылка на магазин]")
    except Exception as e:
        logger.error(f"Error in handle_shop: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
