from aiogram import types
from loguru import logger

from src.bot.handlers.menu.get_main_menu import get_main_menu


async def handle_subscribe(message: types.Message):
    try:
        await message.answer(
            "Чтобы подписаться на Test IT, пожалуйста, посетите следующую ссылку: [ссылка на подписку]")
    except Exception as e:
        logger.error(f"Error in handle_subscribe: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
