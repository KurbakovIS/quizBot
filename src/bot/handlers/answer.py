import re
from aiogram import types
from aiogram.fsm.context import FSMContext
from src.bot.handlers.game import start_game
from src.bot.states import QuizStates
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from loguru import logger


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip()).lower()


async def handle_answer(message: types.Message, state: FSMContext):
    try:
        if message.text.lower() == "подсказка":
            await handle_hint(message, state)
            return

        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            data = await state.get_data()
            question_id = data.get('current_question_id')
            current_level_id = data.get('current_level_id')
            user = await repo.get_user_by_chat_id(str(message.chat.id))

            question = await repo.get_question_by_id(question_id)
            user_answer = normalize_text(message.text)
            correct_answer = normalize_text(question.correct_answer)

            if question and user_answer == correct_answer:
                reward = await repo.get_level_reward(current_level_id)
                await repo.update_user_balance(user.id, reward)
                await repo.mark_level_completed(user.id, current_level_id)
                await message.answer(f"Верно! Вы заработали {reward} points.")

                next_level = await repo.get_next_level(current_level_id)
                if next_level:
                    await repo.add_user_level_entry(user.id, next_level.id)
                    await state.update_data(current_level_id=next_level.id)
                    await start_game(message, state)
                else:
                    await message.answer("Все вопросы завершены.", reply_markup=types.ReplyKeyboardRemove())
                    await state.update_data(quiz_completed=True)
                    await state.set_state(QuizStates.completed)
            else:
                if question.hint:
                    keyboard = types.ReplyKeyboardMarkup(
                        keyboard=[[types.KeyboardButton(text="Подсказка")]],
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                else:
                    keyboard = types.ReplyKeyboardRemove()

                await message.answer("Неправильно. Попробуйте снова.",
                                     reply_markup=keyboard)
                await state.set_state(QuizStates.question)

            current_state = await state.get_state()
            if current_state:
                await repo.update_user_state(user.id, current_state, await state.get_data())
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in handle_answer: {e}")
        await message.answer("Произошла ошибка при обработке ответа. Пожалуйста, попробуйте позже.")


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

            await state.set_state(QuizStates.question)
    except Exception as e:
        logger.error(f"Error in handle_hint: {e}")
        await message.answer("Произошла ошибка при запросе подсказки. Пожалуйста, попробуйте позже.")
