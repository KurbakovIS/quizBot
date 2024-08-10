import re

from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.state_machine import InfoCollectionStates
from src.bot.states import QuizStates
from src.bot.utils.hint import get_question_from_state, generate_hint_message
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database import Level
from src.database.repository import Repository
from src.database.uow import UnitOfWork


def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip()).lower()


async def handle_answer(message: types.Message, state: FSMContext):
    try:
        # Игнорируем команды
        if message.text.startswith('/'):
            await message.answer(
                "Команды меню недоступны во время ответа на вопрос. Завершите ответ и попробуйте снова.")
            return

        if await is_hint_requested(message, state):
            return

        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            data = await state.get_data()

            question = await get_current_question(repo, data)
            if not question:
                await handle_error(message, "Question not found.")
                return

            user_answer = normalize_text(message.text)
            correct_answer = normalize_text(question.correct_answer)

            if user_answer == correct_answer:
                await handle_correct_answer(message, state, repo, data)
            else:
                await handle_incorrect_answer(message, state, question)

            await update_user_state(repo, state, message)
            await uow.commit()
    except Exception as e:
        logger.error(f"Error in handle_answer: {e}")
        await message.answer("Произошла ошибка при обработке ответа. Пожалуйста, попробуйте позже.")


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


async def handle_correct_answer(message: types.Message, state: FSMContext, repo: Repository, data: dict):
    try:
        user = await repo.get_user_by_chat_id(str(message.chat.id))
        current_level_id = data.get('current_level_id')

        reward = await repo.get_level_reward(current_level_id)
        await repo.update_user_balance(user.id, reward)
        await repo.mark_level_completed(user.id, current_level_id)

        await message.answer(f"Верно! Вы заработали {reward} points.")

        next_level = await repo.get_next_level(current_level_id)
        if next_level:
            if next_level.is_object_recognition:
                await state.update_data(current_level_id=next_level.id)
                await start_object_recognition_level(message, state, next_level)
            elif next_level.is_info_collection:
                await start_info_collection_level(message, state, repo, next_level)
            else:
                await state.update_data(current_level_id=next_level.id)
                await message.answer(
                    "Нажмите 'Следующий вопрос' для продолжения или выберите действие из меню.",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[[types.KeyboardButton(text="Следующий вопрос")]],
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                )
                await state.set_state(QuizStates.intermediate)
        else:
            await complete_quiz(message, state)
    except Exception as e:
        logger.error(f"Error handling correct answer: {e}")
        raise


async def handle_incorrect_answer(message: types.Message, state: FSMContext, question):
    try:
        if question.hint:
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Подсказка")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        else:
            keyboard = types.ReplyKeyboardRemove()

        await message.answer("Неправильно. Попробуйте снова.", reply_markup=keyboard)
        await state.set_state(QuizStates.question)
    except Exception as e:
        logger.error(f"Error handling incorrect answer: {e}")
        raise


async def complete_quiz(message: types.Message, state: FSMContext):
    try:
        await message.answer("Все вопросы завершены.", reply_markup=types.ReplyKeyboardRemove())
        await state.update_data(quiz_completed=True, current_level_id=None, current_question_id=None)
        await state.set_state(QuizStates.completed)
    except Exception as e:
        logger.error(f"Error completing quiz: {e}")
        raise


async def update_user_state(repo: Repository, state: FSMContext, message: types.Message):
    try:
        user = await repo.get_user_by_chat_id(str(message.chat.id))
        current_state = await state.get_state()
        if current_state:
            await repo.update_user_state(user.id, current_state, await state.get_data())
    except Exception as e:
        logger.error(f"Error updating user state: {e}")
        raise


async def handle_error(message: types.Message, error_msg: str):
    logger.error(error_msg)
    await message.answer("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.")


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


async def start_info_collection_level(message: types.Message, state: FSMContext, repo: Repository, level: Level):
    """
    Запуск уровня сбора информации. Эта функция задает первый вопрос пользователю и переводит его в состояние сбора информации.

    :param message: Сообщение пользователя, инициирующее начало уровня.
    :param state: Состояние FSM, используемое для отслеживания процесса сбора информации.
    :param repo: Репозиторий для работы с базой данных.
    :param level: Уровень, который обозначен как уровень сбора информации.
    """
    # Отправляем первый вопрос для сбора информации: "Как тебя зовут?"
    await message.answer("Как тебя зовут?")

    # Устанавливаем состояние FSM на первый этап сбора информации
    await state.set_state(InfoCollectionStates.collecting_name)

    # Сохраняем данные о текущем уровне и инициируем словарь для хранения информации о пользователе
    await state.update_data(current_level_id=level.id, user_info={})


async def start_object_recognition_level(message: types.Message, state: FSMContext,  level: Level):
    # Отправляем эталонное изображение с инструкцией для пользователя
    await send_message_with_optional_photo(
        message,
        "Пожалуйста, загрузите фотографию, на которой присутствует указанный объект.",
        level.image_file  # Эталонное изображение
    )

    # Устанавливаем состояние FSM на этап распознавания объекта
    await state.set_state(QuizStates.object_recognition)
