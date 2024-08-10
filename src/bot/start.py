from aiogram import types
from aiogram.fsm.context import FSMContext

from src.bot.handlers.menu.get_main_menu import get_main_menu
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from loguru import logger


async def start_bot(message: types.Message, state: FSMContext):
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


async def get_or_create_user(repo: Repository, message: types.Message):
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


async def restore_user_state(message: types.Message, state: FSMContext, repo: Repository, user_state):
    await state.set_state(user_state.state)
    await state.update_data(**user_state.data)

    current_state = await state.get_state()
    data = await state.get_data()
    current_level_id = data.get('current_level_id')
    current_question_id = data.get('current_question_id')
    quiz_completed = data.get('quiz_completed', False)

    if quiz_completed:
        await message.answer("Все вопросы завершены.")
    elif current_state == QuizStates.question.state and current_question_id:
        question = await repo.get_question_by_id(current_question_id)
        if question:
            await send_message_with_optional_photo(message, question.text, question.image_file)
        else:
            await message.answer("Не удалось загрузить текущий вопрос. Попробуйте снова.")
    elif current_state in [QuizStates.intro.state, QuizStates.start.state]:
        level = await repo.get_level_by_id(current_level_id)
        if level:
            await send_message_with_optional_photo(message, level.intro_text, level.image_file)
            await message.answer(
                "Нажимай Далее для продолжения",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[types.KeyboardButton(text="Далее")]],
                    resize_keyboard=True,
                    one_time_keyboard=True
                )
            )
        else:
            await message.answer("Не удалось загрузить текущий уровень. Попробуйте снова.")
    else:
        await message.answer("Восстановлено предыдущее состояние.")


async def start_new_user(message: types.Message, state: FSMContext, repo: Repository, user):
    level = await repo.get_first_level()
    await repo.update_user_level(user.id, level.id)
    await repo.add_user_level_entry(user.id, level.id)

    await send_message_with_optional_photo(message, level.intro_text, level.image_file)
    await message.answer(
        "Нажимай Далее для продолжения",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Далее")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

    await state.update_data(current_level_id=level.id, intro_levels_completed=0, quiz_completed=False)
    await state.set_state(QuizStates.intro)
    current_state = await state.get_state()
    if current_state:
        await repo.update_user_state(user.id, current_state, await state.get_data())
