from aiogram import types
from loguru import logger

from src.bot.start import get_main_menu


async def handle_comment(message: types.Message):
    try:
        await message.answer("Спасибо за ваш отзыв! Пожалуйста, оставьте его в ответ на это сообщение.", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error in handle_comment: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
