from aiogram import types
from aiogram.fsm.context import FSMContext
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from loguru import logger

async def handle_hint(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            data = await state.get_data()
            question_id = data.get('current_question_id')
            question = await repo.get_question_by_id(question_id)

            if question and question.hint:
                await message.answer(f"Подсказка: {question.hint}")
            else:
                await message.answer("Подсказка недоступна для этого вопроса.")
    except Exception as e:
        logger.error(f"Error in handle_hint: {e}")
        await message.answer("Произошла ошибка при запросе подсказки. Пожалуйста, попробуйте позже.")
