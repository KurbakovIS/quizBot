from aiogram import types
from loguru import logger


async def handle_hide_menu(message: types.Message):
    try:
        await message.answer("Меню скрыто. Вы можете снова открыть его, отправив /start.",
                             reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        logger.error(f"Error in handle_hide_menu: {e}")
        await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")
