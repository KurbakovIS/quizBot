from aiogram import types
from loguru import logger

from src.bot.start import get_main_menu


async def handle_demo(message: types.Message):
    try:
        await message.answer(
            "Чтобы записаться на демо, пожалуйста, заполните форму по следующей ссылке: [ссылка на форму]",
            reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error in handle_demo: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
