import re

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loguru import logger

from src.bot.fsm.state_fsm import InfoCollectionStates
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
        # Проверяем, не нажата ли кнопка "Пропустить уровень"
        if message.text == "Пропустить уровень":
            await skip_level(message, state)
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

        # Переход в состояние intermediate после всех уровней
        await message.answer(
            "Нажмите 'Следующий вопрос' для продолжения или выберите действие из меню.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Следующий вопрос")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        await state.set_state(QuizStates.intermediate)

        # Обновление состояния пользователя
        await update_user_state(repo, state, message)
    except Exception as e:
        logger.error(f"Error handling correct answer: {e}")
        raise


async def handle_incorrect_answer(message: types.Message, state: FSMContext, question):
    try:
        buttons = []
        if question.hint:
            buttons.append([types.KeyboardButton(text="Подсказка")])

        buttons.append([types.KeyboardButton(text="Пропустить уровень")])

        keyboard = types.ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await message.answer("Неправильно. Попробуйте снова или пропустите уровень.", reply_markup=keyboard)
        await state.set_state(QuizStates.question)
    except Exception as e:
        logger.error(f"Error handling incorrect answer: {e}")
        raise


async def complete_quiz(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))

            # Проверяем, есть ли пропущенные уровни
            skipped_levels = await repo.get_skipped_levels(user.id)
            if skipped_levels:
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=level.name)] for level in skipped_levels],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )

                await message.answer(
                    "Все вопросы завершены. Хотите вернуться к пропущенным уровням?",
                    reply_markup=keyboard
                )
                await state.set_state(QuizStates.return_to_skipped)
            else:
                await message.answer("Поздравляем! Вы завершили викторину.")
                await state.set_state(QuizStates.completed)

            # Сохранение обновленного состояния пользователя в базе данных
            await update_user_state(repo, state, message)
            await uow.commit()
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


async def start_info_collection_level(message: types.Message, state: FSMContext, level: Level):
    """
    Запуск уровня сбора информации. Эта функция задает первый вопрос пользователю и переводит его в состояние сбора информации.

    :param message: Сообщение пользователя, инициирующее начало уровня.
    :param state: Состояние FSM, используемое для отслеживания процесса сбора информации.
    :param level: Уровень, который обозначен как уровень сбора информации.
    """
    # Отправляем первый вопрос для сбора информации: "Как тебя зовут?"
    await message.answer("Как тебя зовут?")

    # Устанавливаем состояние FSM на первый этап сбора информации
    await state.set_state(InfoCollectionStates.collecting_name)

    # Сохраняем данные о текущем уровне и инициируем словарь для хранения информации о пользователе
    await state.update_data(current_level_id=level.id, user_info={})


async def start_object_recognition_level(message: types.Message, state: FSMContext, level: Level):
    # Отправляем эталонное изображение с инструкцией для пользователя
    await send_message_with_optional_photo(
        message,
        "Пожалуйста, загрузите фотографию, на которой присутствует указанный объект.",
        level.image_file  # Эталонное изображение
    )

    # Устанавливаем состояние FSM на этап распознавания объекта
    await state.set_state(QuizStates.object_recognition)


async def start_intro_level(message: types.Message, state: FSMContext, repo: Repository, level: Level):
    try:
        # Отправляем интро текст уровня и, если доступно, изображение
        await send_message_with_optional_photo(message, level.intro_text, level.image_file)

        # Переход в состояние интро уровня
        await state.set_state(QuizStates.intro)

        # Обновляем текущее состояние пользователя в базе данных
        current_state = await state.get_state()
        if current_state:
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            await repo.update_user_state(user.id, current_state, await state.get_data())

        # Если есть инструкции для перехода к следующему этапу, добавляем их
        await message.answer(
            "Нажмите 'Далее', чтобы продолжить.",
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="Далее")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
    except Exception as e:
        logger.error(f"Error in start_intro_level: {e}")
        await message.answer("Произошла ошибка при запуске интро уровня. Пожалуйста, попробуйте позже.")


async def skip_level(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        current_level_id = data.get('current_level_id')
        user = await repo.get_user_by_chat_id(str(message.chat.id))

        # Отмечаем уровень как пропущенный
        await repo.mark_level_skipped(user.id, current_level_id)
        await uow.commit()

        # Проверяем, есть ли еще уровни
        next_level = await repo.get_next_level(current_level_id)

        if next_level:
            await state.update_data(current_level_id=next_level.id)

            # Переход на следующий уровень или промежуточное состояние
            if next_level.is_intro:
                await start_intro_level(message, state, repo, next_level)
            elif next_level.is_object_recognition:
                await start_object_recognition_level(message, state, next_level)
            elif next_level.is_info_collection:
                await start_info_collection_level(message, state, next_level)
            else:
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
            # Все уровни завершены, переходим в состояние completed
            await state.update_data(quiz_completed=True)
            await state.set_state(QuizStates.completed)
            await message.answer("Все вопросы завершены.", reply_markup=types.ReplyKeyboardRemove())

        # Обновляем состояние пользователя в базе данных
        await update_user_state(repo, state, message)


async def return_to_skipped_levels(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))

            skipped_levels = await repo.get_skipped_levels(user.id)
            if skipped_levels:
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                buttons = [types.KeyboardButton(text=level.name) for level in skipped_levels]
                keyboard.keyboard.extend([[button] for button in buttons])

                await message.answer("Выберите пропущенный уровень для возврата:", reply_markup=keyboard)
                await state.set_state(QuizStates.return_to_skipped)
            else:
                await message.answer("Нет пропущенных уровней.")
                await state.set_state(QuizStates.completed)
    except Exception as e:
        logger.error(f"Error in return_to_skipped_levels: {e}")
        await message.answer("Произошла ошибка при возврате к пропущенным уровням. Пожалуйста, попробуйте позже.")


async def handle_skipped_level_choice(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            level_name = message.text
            skipped_level = await repo.get_skipped_level_by_name(user.id, level_name)

            if skipped_level:
                await state.update_data(current_level_id=skipped_level.id)
                await start_level(message, state, repo, skipped_level)

                # Удаление из пропущенных уровней
                await repo.remove_skipped_level(user.id, skipped_level.id)

                # Обновляем состояние пользователя
                await update_user_state(repo, state, message)

                await uow.commit()
            else:
                await message.answer("Указанный уровень не найден среди пропущенных.")
                await state.set_state(QuizStates.completed)
    except Exception as e:
        logger.error(f"Error in handle_skipped_level_choice: {e}")
        await message.answer("Произошла ошибка при выборе пропущенного уровня. Пожалуйста, попробуйте позже.")


async def handle_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_level_id = data.get('current_level_id')

    async with UnitOfWork() as uow:
        repo = Repository(uow.session)

        # Получаем следующий уровень
        next_level = await repo.get_next_level(current_level_id)

        if next_level:
            # Обновляем текущее состояние на следующий уровень
            await state.update_data(current_level_id=next_level.id)
            await start_level(message, state, repo, next_level)
        else:
            # Если уровней больше нет, переводим пользователя в состояние completed
            await complete_quiz(message, state)


async def start_level(message: types.Message, state: FSMContext, repo: Repository, level: Level):
    try:
        await state.update_data(current_question_id=None)
        if level.is_intro:
            await start_intro_level(message, state, repo, level)
        elif level.is_object_recognition:
            await start_object_recognition_level(message, state, level)
        elif level.is_info_collection:
            await start_info_collection_level(message, state, level)
        else:
            questions = await repo.get_questions_by_level(level.id)
            if questions:
                question = questions[0]
                await send_message_with_optional_photo(message, question.text, question.image_file)
                await state.update_data(current_question_id=question.id)
                await state.set_state(QuizStates.question)
            else:
                await message.answer("Уровень не содержит вопросов.")
                await state.set_state(QuizStates.completed)
    except Exception as e:
        logger.error(f"Error in start_level: {e}")
        await message.answer("Произошла ошибка при старте уровня. Пожалуйста, попробуйте позже.")


async def skip_completed_levels(message: types.Message, state: FSMContext, repo: Repository, user_id: str,
                                current_level: Level):
    try:
        completed_levels = await repo.get_completed_levels(user_id)
        next_level = await repo.get_next_level(current_level.id)

        while next_level and next_level.id in completed_levels:
            next_level = await repo.get_next_level(next_level.id)

        if next_level:
            await state.update_data(current_level_id=next_level.id)
            await start_level(message, state, repo, next_level)
        else:
            await complete_quiz(message, state)
    except Exception as e:
        logger.error(f"Error skipping completed levels: {e}")
        raise
