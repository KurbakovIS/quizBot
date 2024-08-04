from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.start import start_bot


async def handle_menu_start(message: types.Message, state: FSMContext):
    try:
        await start_bot(message, state)
    except Exception as e:
        logger.error(f"Error in handle_menu_start: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
