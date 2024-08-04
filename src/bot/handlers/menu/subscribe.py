from aiogram import types
from loguru import logger

from src.bot.start import get_main_menu


async def handle_subscribe(message: types.Message):
    try:
        await message.answer(
            "Чтобы подписаться на Test IT, пожалуйста, посетите следующую ссылку: [ссылка на подписку]",
            reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error in handle_subscribe: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
