from aiogram import types
from aiogram.fsm.context import FSMContext

from src.bot.states import QuizStates
from src.bot.utils.errors import handle_error
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.bot.utils.state_management import update_user_state
from src.database import User, Level
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def continue_intro(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user, data = await get_user_and_state_data(repo, message, state)

            next_level = await repo.get_next_level(data.get('current_level_id'))
            if next_level:
                await handle_level_transition(message, state, repo, user, next_level, data)
            else:
                await handle_no_more_levels(message, state)

            await update_user_state(repo, state, user.id)
            await uow.commit()
    except Exception as e:
        await handle_error(message, "Error in continue_intro", e)


async def handle_level_transition(message: types.Message, state: FSMContext, repo: Repository, user: User,
                                  next_level: Level, data: dict):
    if next_level.is_intro:
        await handle_intro_level(message, state, repo, user, next_level, data)
    else:
        await start_quiz(message, state, repo, user, next_level)


async def get_user_and_state_data(repo: Repository, message: types.Message, state: FSMContext):
    user = await repo.get_user_by_chat_id(str(message.chat.id))
    data = await state.get_data()
    return user, data


async def handle_intro_level(message, state, repo, user, next_level, data):
    intro_levels_completed = data.get('intro_levels_completed', 0)
    await send_message_with_optional_photo(message, next_level.intro_text, next_level.image_file)
    await update_user_level_data(repo, user, next_level)
    await state.update_data(current_level_id=next_level.id, intro_levels_completed=intro_levels_completed + 1)
    await state.set_state(QuizStates.intro)


async def start_quiz(message, state, repo, user, next_level):
    await message.answer(
        "Викторина начинается. Нажмите 'Далее' для первого вопроса.",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="Далее")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    await update_user_level_data(repo, user, next_level)
    await state.update_data(current_level_id=next_level.id)
    await state.set_state(QuizStates.start)


async def update_user_level_data(repo: Repository, user, next_level):
    await repo.add_user_level_entry(user.id, next_level.id)
    await repo.add_stage_completion(user.id, next_level.id)
    await repo.update_user_level(user.id, next_level.id)


async def handle_no_more_levels(message, state):
    await message.answer(
        "Все уровни Intro завершены, но уровни с вопросами не найдены.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.clear()
