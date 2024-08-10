from aiogram import types
from aiogram.fsm.context import FSMContext

from loguru import logger

from src.bot.utils.hint import get_question_from_state, generate_hint_message


async def handle_hint(message: types.Message, state: FSMContext):
    try:
        question = await get_question_from_state(state)
        hint_text = generate_hint_message(question)
        await message.answer(hint_text)
    except Exception as e:
        logger.error(f"Error in handle_hint: {e}")
        await message.answer("Произошла ошибка при запросе подсказки. Пожалуйста, попробуйте позже.")



