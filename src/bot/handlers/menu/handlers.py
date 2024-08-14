from aiogram import types
from loguru import logger
from aiogram.fsm.context import FSMContext

from src.bot.start import start_bot


async def handle_error(message: types.Message, exception: Exception):
    logger.error(f"Error: {exception}")
    await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")


async def handle_menu_start(message: types.Message, state: FSMContext):
    try:
        await start_bot(message, state)
    except Exception as e:
        await handle_error(message, e)


async def handle_hide_menu(message: types.Message):
    try:
        await message.answer("Меню скрыто. Вы можете снова открыть его, отправив /start.",
                             reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        await handle_error(message, e)


async def handle_comment(message: types.Message):
    try:
        await message.answer("Спасибо за ваш отзыв! Пожалуйста, оставьте его в ответ на это сообщение.")
    except Exception as e:
        await handle_error(message, e)


async def handle_demo(message: types.Message):
    try:
        await message.answer(
            "Чтобы записаться на демо, пожалуйста, заполните форму по следующей ссылке: [ссылка на форму]")
    except Exception as e:
        await handle_error(message, e)


async def handle_shop(message: types.Message):
    try:
        await message.answer(
            "Добро пожаловать в наш магазин мерча! Пожалуйста, посетите следующую ссылку для покупок: [ссылка на магазин]")
    except Exception as e:
        await handle_error(message, e)


async def handle_info(message: types.Message):
    try:
        await message.answer(
            "Test IT - это платформа для тестирования ваших знаний в области информационных технологий. Мы предлагаем разнообразные викторины и тесты, чтобы помочь вам улучшить свои навыки.")
    except Exception as e:
        await handle_error(message, e)


async def handle_subscribe(message: types.Message):
    try:
        await message.answer(
            "Чтобы подписаться на Test IT, пожалуйста, посетите следующую ссылку: [ссылка на подписку]")
    except Exception as e:
        await handle_error(message, e)
