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
                question = questions[0]
                await send_message_with_optional_photo(message, question.text, question.image_file)
                await state.update_data(current_question_id=question.id)
                await repo.add_stage_completion(user.id, current_level_id)
                await state.set_state(QuizStates.question)
            else:
                next_level = await repo.get_next_level(current_level_id)
                if next_level:
                    await state.update_data(current_level_id=next_level.id)
                    await start_game(message, state)
                else:
                    await message.answer("Нет доступных вопросов на данный момент.",
                                         reply_markup=types.ReplyKeyboardRemove())
                    await state.clear()
            current_state = await state.get_state()
            if current_state:
                await repo.update_user_state(user.id, current_state, await state.get_data())
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in start_game: {e}")
        await message.answer("Произошла ошибка при запуске игры. Пожалуйста, попробуйте позже.")
