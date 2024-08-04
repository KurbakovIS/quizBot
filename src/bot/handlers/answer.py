from aiogram import types
from aiogram.fsm.context import FSMContext

from src.bot.handlers.game import start_game
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def handle_answer(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        question_id = data.get('current_question_id')
        current_level_id = data.get('current_level_id')
        user = await repo.get_user_by_chat_id(str(message.chat.id))

        question = await repo.get_question_by_id(question_id)

        if question and message.text.lower() == question.correct_answer.lower():
            reward = await repo.get_level_reward(current_level_id)
            await repo.update_user_balance(user.id, reward)
            await repo.mark_level_completed(user.id, current_level_id)
            await message.answer(f"Верно! Вы заработали {reward} points.")
        else:
            await message.answer("Неправильно. Попробуйте снова.")

        next_level = await repo.get_next_level(current_level_id)
        if next_level:
            await repo.add_user_level_entry(user.id, next_level.id)
            await state.update_data(current_level_id=next_level.id)
            await start_game(message, state)
        else:
            await message.answer("Все вопросы завершены.", reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
        current_state = await state.get_state()
        if current_state:
            await repo.update_user_state(user.id, current_state, await state.get_data())
        await uow.commit()
