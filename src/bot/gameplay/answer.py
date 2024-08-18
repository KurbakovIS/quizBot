import re

from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.states import QuizStates
from src.bot.utils.errors import handle_error_answer
from src.bot.utils.hint import get_question_from_state, generate_hint_message
from src.bot.utils.levels import skip_level, start_level
from src.bot.utils.state_management import update_user_state
from src.database.repository import Repository
from src.database.uow import UnitOfWork


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip()).lower()


async def handle_answer(message: types.Message, state: FSMContext):
    try:
        if message.text.startswith('/'):
            await message.answer(
                "Команды меню недоступны во время ответа на вопрос. Завершите ответ и попробуйте снова.")
            return

        if message.text == "Пропустить уровень":
            async with UnitOfWork() as uow:
                repo = Repository(uow.session)
                await skip_level(message, state, repo)
            return

        if await is_hint_requested(message, state):
            return

        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            data = await state.get_data()
            question = await get_current_question(repo, data)

            if not question:
                await handle_error_answer(message, "Question not found.")
                return

            user_answer = normalize_text(message.text)
            correct_answer = normalize_text(question.correct_answer)

            if user_answer == correct_answer:
                await handle_correct_answer(message, state, repo, data)
            else:
                await handle_incorrect_answer(message, state, question)

            await update_user_state(repo, state, user.id)
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in handle_answer: {e}")
        await message.answer("Произошла ошибка при обработке ответа. Пожалуйста, попробуйте позже.")


async def handle_correct_answer(message: types.Message, state: FSMContext, repo: Repository, data: dict):
    try:
        user = await repo.get_user_by_chat_id(str(message.chat.id))
        current_level_id = data.get('current_level_id')

        reward = await repo.get_level_reward(current_level_id)
        await repo.update_user_balance(user.id, reward)
        await repo.mark_level_completed(user.id, current_level_id)

        await message.answer(f"Верно! Вы заработали {reward} points.")
        await prompt_next_action(message, state)
    except Exception as e:
        logger.error(f"Error handling correct answer: {e}")
        raise


async def handle_incorrect_answer(message: types.Message, state: FSMContext, question):
    try:
        buttons = [types.KeyboardButton(text="Пропустить уровень")]
        if question.hint:
            buttons.insert(0, types.KeyboardButton(text="Подсказка"))

        keyboard = types.ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True, one_time_keyboard=True)
        await message.answer("Неправильно. Попробуйте снова или пропустите уровень.", reply_markup=keyboard)
        await state.set_state(QuizStates.question)
    except Exception as e:
        logger.error(f"Error handling incorrect answer: {e}")
        raise


async def is_hint_requested(message: types.Message, state: FSMContext) -> bool:
    if message.text.lower() == "подсказка":
        await handle_hint(message, state)
        return True
    return False


async def get_current_question(repo: Repository, data: dict):
    question_id = data.get('current_question_id')
    if question_id is None:
        return None
    return await repo.get_question_by_id(question_id)


async def handle_hint(message: types.Message, state: FSMContext):
    try:
        question = await get_question_from_state(state)
        if not question:
            await message.answer("Вопрос не найден.")
            return

        hint_text = generate_hint_message(question)
        await message.answer(hint_text)

        await state.set_state(QuizStates.question)
    except Exception as e:
        logger.error(f"Error in handle_hint: {e}")
        await message.answer("Произошла ошибка при запросе подсказки. Пожалуйста, попробуйте позже.")


async def complete_quiz(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))

            skipped_levels = await repo.get_skipped_levels(user.id)
            if skipped_levels:
                keyboard = types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text=level.name)] for level in skipped_levels],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )

                await message.answer("Все вопросы завершены. Хотите вернуться к пропущенным уровням?",
                                     reply_markup=keyboard)
                await state.set_state(QuizStates.return_to_skipped)
            else:
                await message.answer("Поздравляем! Вы завершили викторину.", reply_markup=types.ReplyKeyboardRemove())
                await state.set_state(QuizStates.completed)

            await update_user_state(repo, state, user.id)
            await uow.commit()
    except Exception as e:
        logger.error(f"Error completing quiz: {e}")
        raise


async def prompt_next_action(message: types.Message, state: FSMContext):
    await message.answer(
        "Нажмите 'Следующий вопрос' для продолжения или выберите действие из меню.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Следующий вопрос")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await state.set_state(QuizStates.intermediate)


async def handle_next_question(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        current_level_id = data.get('current_level_id')

        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            # Получаем следующий уровень
            next_level = await repo.get_next_level(current_level_id)

            if next_level:
                # Обновляем текущее состояние на следующий уровень
                await state.update_data(current_level_id=next_level.id)
                await start_level(message, state, repo, next_level, user.id)
            else:
                # Если уровней больше нет, переводим пользователя в состояние completed
                await complete_quiz(message, state)
            await uow.commit()
    except Exception as e:
        await handle_error_answer(message, f"Error in handle_next_question: {e}")


async def return_to_skipped_levels(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))

            skipped_levels = await repo.get_skipped_levels(user.id)
            if skipped_levels:
                keyboard = types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text=level.name)] for level in skipped_levels],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )

                await message.answer("Выберите пропущенный уровень для возврата:", reply_markup=keyboard)
                await state.set_state(QuizStates.return_to_skipped)
            else:
                await message.answer("Нет пропущенных уровней.")
                await state.set_state(QuizStates.completed)
            await uow.commit()
    except Exception as e:
        await handle_error_answer(message, f"Error in return_to_skipped_levels: {e}")


async def handle_skipped_level_choice(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            level_name = message.text
            skipped_level = await repo.get_skipped_level_by_name(user.id, level_name)

            if skipped_level:
                await state.update_data(current_level_id=skipped_level.id)
                await start_level(message, state, repo, skipped_level, user.id)

                # Удаление из пропущенных уровней
                await repo.remove_skipped_level(user.id, skipped_level.id)

                # Обновляем состояние пользователя
                await update_user_state(repo, state, user.id)

                await uow.commit()
            else:
                await message.answer("Указанный уровень не найден среди пропущенных.")
                await state.set_state(QuizStates.completed)
    except Exception as e:
        await handle_error_answer(message, f"Error in handle_skipped_level_choice: {e}")
