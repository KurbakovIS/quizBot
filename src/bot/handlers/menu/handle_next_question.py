from aiogram import types
from aiogram.fsm.context import FSMContext

from src.bot.handlers.answer import start_intro_level, start_object_recognition_level, start_info_collection_level, \
    complete_quiz
from src.bot.handlers.game import handle_no_questions_available
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def handle_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_level_id = data.get('current_level_id')

    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        next_level = await repo.get_next_level(current_level_id)

        if next_level:
            await state.update_data(current_level_id=next_level.id)

            if next_level.is_intro:
                await start_intro_level(message, state, repo, next_level)
            elif next_level.is_object_recognition:
                await start_object_recognition_level(message, state, next_level)
            elif next_level.is_info_collection:
                await start_info_collection_level(message, state, next_level)
            else:
                questions = await repo.get_questions_by_level(next_level.id)
                if questions:
                    question = questions[0]
                    await send_message_with_optional_photo(message, question.text, question.image_file)
                    await state.update_data(current_question_id=question.id)
                    await state.set_state(QuizStates.question)
                else:
                    await handle_no_questions_available(message, state, repo, next_level.id)
        else:
            await complete_quiz(message, state)
