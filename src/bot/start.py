from uuid import UUID

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from loguru import logger

from src.bot.fsm.state_fsm import InfoCollectionStates
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.bot.utils.state_management import update_user_state
from src.database import User
from src.database.repository import Repository
from src.database.uow import UnitOfWork


# Обобщенные функции для работы с клавиатурой
def create_single_button_keyboard(button_text: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button_text)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def handle_quiz_completion(message: types.Message, state: FSMContext, repo: Repository, user_state) -> None:
    skipped_levels = await repo.get_skipped_levels(user_state.user_id)
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
        await message.answer("Все вопросы завершены. Поздравляем! Вы завершили викторину.",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state(QuizStates.completed)
        await update_user_state(repo, state, user_state.user_id)


async def handle_object_recognition(message: types.Message, repo: Repository, current_level_id: UUID) -> None:
    level = await repo.get_level_by_id(current_level_id)
    if level:
        await send_message_with_optional_photo(
            message,
            "Пожалуйста, загрузите фотографию, на которой присутствует указанный объект.",
            level.image_file
        )


async def handle_question_state(message: types.Message, repo: Repository, current_question_id: UUID) -> None:
    question = await repo.get_question_by_id(current_question_id)
    if question:
        await send_message_with_optional_photo(message, question.text, question.image_file)


async def handle_info_collection(message: types.Message, state: FSMContext, current_state: str) -> None:
    user_info = (await state.get_data()).get('user_info', {})
    if current_state == InfoCollectionStates.collecting_name.state:
        await message.answer("Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
    elif current_state == InfoCollectionStates.collecting_company.state:
        await message.answer("В какой компании ты работаешь?", reply_markup=ReplyKeyboardRemove())
    elif current_state == InfoCollectionStates.collecting_position.state:
        await message.answer("Какая у тебя должность?", reply_markup=ReplyKeyboardRemove())
    elif current_state == InfoCollectionStates.confirmation.state:
        info_text = (f"Имя: {user_info.get('name', '')}\n"
                     f"Компания: {user_info.get('company', '')}\n"
                     f"Должность: {user_info.get('position', '')}\n"
                     "Всё верно?")
        await message.answer(info_text, reply_markup=create_single_button_keyboard("Да"))


async def start_bot(message: types.Message, state: FSMContext) -> None:
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await get_or_create_user(repo, message)
            user_state = await repo.get_user_state(user.id)

            if user_state:
                await restore_user_state(message, state, repo, user_state)
            else:
                await start_new_user(message, state, repo, user)

            await uow.commit()
    except Exception as e:
        logger.error(f"Error in start_bot: {e}")
        await message.answer("Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже.")


async def get_or_create_user(repo: Repository, message: types.Message) -> 'User':
    user = await repo.get_user_by_chat_id(str(message.chat.id))
    if not user:
        level = await repo.get_first_level()
        user = await repo.create_user(
            username=message.from_user.username,
            chat_id=str(message.chat.id),
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            current_level=level.id,
        )
    return user


async def restore_user_state(message: types.Message, state: FSMContext, repo: Repository, user_state) -> None:
    await state.set_state(user_state.state)
    await state.update_data(**user_state.data)

    current_state = await state.get_state()
    data = await state.get_data()
    current_level_id = data.get('current_level_id')
    current_question_id = data.get('current_question_id')

    if data.get('quiz_completed', False) or current_state == QuizStates.return_to_skipped:
        await handle_quiz_completion(message, state, repo, user_state)
    elif current_state == QuizStates.object_recognition.state and current_level_id:
        await handle_object_recognition(message, repo, current_level_id)
    elif current_state == QuizStates.question.state and current_question_id:
        await handle_question_state(message, repo, current_question_id)
    elif current_state == QuizStates.intermediate.state:
        await message.answer(
            "Нажмите 'Следующий вопрос' для продолжения или выберите действие из меню.",
            reply_markup=create_single_button_keyboard("Следующий вопрос")
        )
    elif current_state in [
        InfoCollectionStates.collecting_name.state,
        InfoCollectionStates.collecting_company.state,
        InfoCollectionStates.collecting_position.state,
        InfoCollectionStates.confirmation.state,
    ]:
        await handle_info_collection(message, state, current_state)
    elif current_state in [QuizStates.intro.state, QuizStates.start.state]:
        level = await repo.get_level_by_id(current_level_id)
        if level:
            await send_message_with_optional_photo(message, level.intro_text, level.image_file)
            await message.answer(
                "Нажимай Далее для продолжения",
                reply_markup=create_single_button_keyboard("Далее")
            )
    else:
        await message.answer("Восстановлено предыдущее состояние.", reply_markup=ReplyKeyboardRemove())


async def start_new_user(message: types.Message, state: FSMContext, repo: Repository, user: User) -> None:
    level = await repo.get_first_level()
    await repo.update_user_level(user.id, level.id)
    await repo.add_user_level_entry(user.id, level.id)

    await send_message_with_optional_photo(message, level.intro_text, level.image_file)
    await message.answer(
        "Нажимай Далее для продолжения",
        reply_markup=create_single_button_keyboard("Далее")
    )

    await state.update_data(current_level_id=level.id, intro_levels_completed=0, quiz_completed=False)
    await state.set_state(QuizStates.intro)
    await repo.update_user_state(user.id, await state.get_state(), await state.get_data())
