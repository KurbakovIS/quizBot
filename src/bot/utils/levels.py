from uuid import UUID

from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.fsm.state_fsm import InfoCollectionStates
from src.bot.states import QuizStates
from src.bot.utils.errors import handle_error_answer
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.bot.utils.state_management import update_user_state
from src.database import Level
from src.database.repository import Repository


async def start_level(message: types.Message, state: FSMContext, repo: Repository, level: Level, user_id):
    await state.update_data(current_question_id=None)
    if level.is_intro:
        await start_intro_level(message, state, repo, level)
    elif level.is_object_recognition:
        await repo.add_user_level_entry(user_id, level.id)
        await start_object_recognition_level(message, state, level, repo, user_id)
    elif level.is_info_collection:
        await repo.add_user_level_entry(user_id, level.id)
        await start_info_collection_level(message, state, level.id, repo, user_id)
    else:
        await repo.add_user_level_entry(user_id, level.id)
        questions = await repo.get_questions_by_level(level.id)
        if questions:
            question = questions[0]
            await send_message_with_optional_photo(message, question.text, question.image_file)
            await state.update_data(current_question_id=question.id)
            await state.set_state(QuizStates.question)
            await update_user_state(repo, state, user_id)
        else:
            await message.answer("Уровень не содержит вопросов.")
            await state.set_state(QuizStates.completed)
            await update_user_state(repo, state, user_id)


async def start_intro_level(message: types.Message, state: FSMContext, repo: Repository, level: Level):
    try:
        await send_message_with_optional_photo(message, level.intro_text, level.image_file)
        await state.set_state(QuizStates.intro)

        current_state = await state.get_state()
        if current_state:
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            await repo.update_user_state(user.id, current_state, await state.get_data())

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


async def start_object_recognition_level(message: types.Message, state: FSMContext, level: Level, repo, user_id):
    await send_message_with_optional_photo(
        message,
        "Пожалуйста, загрузите фотографию, на которой присутствует указанный объект.",
        level.image_file
    )
    await state.set_state(QuizStates.object_recognition)
    await update_user_state(repo, state, user_id)


async def start_info_collection_level(message: types.Message, state: FSMContext, current_level_id: UUID,
                                      repo: Repository, user_id):
    await message.answer("Как тебя зовут?")
    await state.set_state(InfoCollectionStates.collecting_name)
    await update_user_state(repo, state, user_id)
    await state.update_data(current_level_id=current_level_id, user_info={})


async def skip_level(message: types.Message, state: FSMContext, repo: Repository):
    try:
        data = await state.get_data()
        current_level_id = data.get('current_level_id')
        user = await repo.get_user_by_chat_id(str(message.chat.id))

        # Отмечаем уровень как пропущенный
        await repo.mark_level_skipped(user.id, current_level_id)

        # Переход к следующему уровню
        next_level = await repo.get_next_level(current_level_id, user.id)
        if next_level:
            await state.update_data(current_level_id=next_level.id)

            # Переход на следующий уровень или промежуточное состояние
            if next_level.is_intro:
                await start_intro_level(message, state, repo, next_level)
            elif next_level.is_object_recognition:
                await repo.add_user_level_entry(user.id, current_level_id)
                await start_object_recognition_level(message, state, next_level, repo, user.id)
            elif next_level.is_info_collection:
                await repo.add_user_level_entry(user.id, current_level_id)
                await start_info_collection_level(message, state, next_level.id, repo, user.id)
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
        await update_user_state(repo, state, user.id)
    except Exception as e:
        logger.error(f"Error in skip_level: {e}")
        await handle_error_answer(message, "Произошла ошибка при пропуске уровня.")
