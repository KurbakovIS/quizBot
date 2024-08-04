from aiogram import types
from aiogram.fsm.context import FSMContext
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from loguru import logger

async def continue_intro(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            data = await state.get_data()
            current_level_id = data.get('current_level_id')
            intro_levels_completed = data.get('intro_levels_completed')
            user = await repo.get_user_by_chat_id(str(message.chat.id))

            next_level = await repo.get_next_level(current_level_id)
            if next_level and next_level.is_intro:
                await send_message_with_optional_photo(message, next_level.intro_text, next_level.image_file)
                await repo.add_user_level_entry(user.id, next_level.id)
                await repo.add_stage_completion(user.id, next_level.id)
                await repo.update_user_level(user.id, next_level.id)
                await state.update_data(current_level_id=next_level.id, intro_levels_completed=intro_levels_completed + 1)
                await state.set_state(QuizStates.intro)
            else:
                if next_level:
                    await message.answer("Викторина начинается. Нажмите 'Далее' для первого вопроса.",
                                         reply_markup=types.ReplyKeyboardMarkup(
                                             keyboard=[
                                                 [
                                                     types.KeyboardButton(text="Далее")
                                                 ]
                                             ],
                                             resize_keyboard=True,
                                             one_time_keyboard=True
                                         ))
                    await repo.add_user_level_entry(user.id, next_level.id)
                    await repo.add_stage_completion(user.id, next_level.id)
                    await repo.update_user_level(user.id, next_level.id)
                    await state.update_data(current_level_id=next_level.id)
                    await state.set_state(QuizStates.start)
                else:
                    await message.answer("Все уровни Intro завершены, но уровни с вопросами не найдены.",
                                         reply_markup=types.ReplyKeyboardRemove())
                    await state.clear()
            current_state = await state.get_state()
            if current_state:
                await repo.update_user_state(user.id, current_state, await state.get_data())
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in continue_intro: {e}")
        await message.answer("Произошла ошибка при продолжении. Пожалуйста, попробуйте позже.")
