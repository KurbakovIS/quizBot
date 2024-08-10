from aiogram import types
from aiogram.fsm.context import FSMContext
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from loguru import logger


async def start_game(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            data = await state.get_data()

            current_level_id = data.get('current_level_id')
            user = await repo.get_user_by_chat_id(str(message.chat.id))

            questions = await repo.get_questions_by_level(current_level_id)
            if questions:
                await handle_existing_questions(message, state, repo, user, current_level_id, questions)
            else:
                await handle_no_questions_available(message, state, repo, current_level_id)

            await update_user_state(repo, state, user)
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in start_game: {e}")
        await message.answer("Произошла ошибка при запуске игры. Пожалуйста, попробуйте позже.")


async def handle_existing_questions(message: types.Message, state: FSMContext, repo: Repository, user, current_level_id,
                                    questions):
    try:
        question = questions[0]
        await send_message_with_optional_photo(message, question.text, question.image_file)
        await state.update_data(current_question_id=question.id)
        await repo.add_stage_completion(user.id, current_level_id)
        await state.set_state(QuizStates.question)
    except Exception as e:
        logger.error(f"Error in handle_existing_questions: {e}")
        raise


async def handle_no_questions_available(message: types.Message, state: FSMContext, repo: Repository, current_level_id):
    try:
        next_level = await repo.get_next_level(current_level_id)
        if next_level:
            await state.update_data(current_level_id=next_level.id)
            await start_game(message, state)
        else:
            await message.answer("Нет доступных вопросов на данный момент.",
                                 reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
    except Exception as e:
        logger.error(f"Error in handle_no_questions_available: {e}")
        raise


async def update_user_state(repo: Repository, state: FSMContext, user):
    try:
        current_state = await state.get_state()
        if current_state:
            await repo.update_user_state(user.id, current_state, await state.get_data())
    except Exception as e:
        logger.error(f"Error in update_user_state: {e}")
        raise
