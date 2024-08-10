from src.bot.handlers.game import handle_no_questions_available
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from aiogram import types
from aiogram.fsm.context import FSMContext

async def handle_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_level_id = data.get('current_level_id')

    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        questions = await repo.get_questions_by_level(current_level_id)
        if questions:
            question = questions[0]
            await send_message_with_optional_photo(message, question.text, question.image_file)
            await state.update_data(current_question_id=question.id)
            await state.set_state(QuizStates.question)
        else:
            await handle_no_questions_available(message, state, repo, current_level_id)
