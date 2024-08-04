from aiogram import types
from loguru import logger

from src.bot.start import get_main_menu


async def handle_shop(message: types.Message):
    try:
        await message.answer(
            "Добро пожаловать в наш магазин мерча! Пожалуйста, посетите следующую ссылку для покупок: [ссылка на магазин]",
            reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error in handle_shop: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
