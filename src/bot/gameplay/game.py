from typing import Optional
from uuid import UUID

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from loguru import logger

from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database import Question
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def start_game(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user, current_level_id, question = await fetch_game_data(repo, state, message)

            if question:
                await process_question(message, state, question)
            else:
                await process_next_level_or_finish(message, state, repo, current_level_id, user.id)

            await finalize_game_state(repo, state, user.id)
            await uow.commit()
    except Exception as e:
        await handle_game_error(message, "Error in start_game", e)


async def fetch_game_data(repo: Repository, state: FSMContext, message: types.Message):
    data = await state.get_data()
    current_level_id = data.get('current_level_id')
    user = await repo.get_user_by_chat_id(str(message.chat.id))
    question = await repo.get_random_question_by_level(current_level_id)
    return user, current_level_id, question


async def process_question(message: types.Message, state: FSMContext, question: Question):
    try:
        await send_message_with_optional_photo(message, question.text, question.image_file)
        await update_state(state, current_question_id=question.id, new_state=QuizStates.question.state)
    except Exception as e:
        await handle_game_error(message, "Error in process_questions", e)
        raise


async def process_next_level_or_finish(message: types.Message, state: FSMContext, repo: Repository,
                                       current_level_id: UUID, user_id):
    try:
        next_level = await repo.get_next_level(current_level_id, user_id)
        if next_level:
            await update_state(state, current_level_id=next_level.id)
            await start_game(message, state)  # Рекурсивный вызов для обработки следующего уровня.
        else:
            await message.answer("Нет доступных вопросов на данный момент.",
                                 reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
    except Exception as e:
        await handle_game_error(message, "Error in process_next_level_or_finish", e)
        raise


async def update_state(state: FSMContext, current_question_id: UUID = None,
                       current_level_id: UUID = None, new_state: State = None):
    """Обновляет состояние FSMContext, если переданы соответствующие аргументы."""
    if current_question_id:
        await state.update_data(current_question_id=current_question_id)
    if current_level_id:
        await state.update_data(current_level_id=current_level_id)
    if new_state:
        await state.set_state(new_state)


async def finalize_game_state(repo: Repository, state: FSMContext, user_id: UUID):
    try:
        current_state = await state.get_state()
        if current_state:
            await repo.update_user_state(user_id, current_state, await state.get_data())
    except Exception as e:
        await handle_game_error(None, "Error in finalize_game_state", e)
        raise


async def handle_game_error(message: Optional[types.Message], context: str, exception: Exception):
    logger.error(f"{context}: {exception}")
    if message:
        await message.answer("Произошла ошибка при запуске игры. Пожалуйста, попробуйте позже.")
