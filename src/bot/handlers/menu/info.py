from aiogram import types
from loguru import logger

from src.bot.start import get_main_menu


async def handle_info(message: types.Message):
    try:
        await message.answer(
            "Test IT - это платформа для тестирования ваших знаний в области информационных технологий. Мы предлагаем разнообразные викторины и тесты, чтобы помочь вам улучшить свои навыки.",
            reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Error in handle_info: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
