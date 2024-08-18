from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.fsm.state_fsm import InfoCollectionStates
from src.bot.gameplay.answer import update_user_state
from src.bot.states import QuizStates
from src.bot.utils.errors import handle_error
from src.bot.utils.levels import start_info_collection_level
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def collect_name(message: types.Message, state: FSMContext):
    await collect_user_info(message, state, 'name', "В какой компании ты работаешь?",
                            InfoCollectionStates.collecting_company)


async def collect_company(message: types.Message, state: FSMContext):
    await collect_user_info(message, state, 'company', "Какая у тебя должность?",
                            InfoCollectionStates.collecting_position)


async def collect_position(message: types.Message, state: FSMContext):
    try:
        await collect_user_info(message, state, 'position', None, InfoCollectionStates.confirmation)

        data = await state.get_data()
        user_info = data.get('user_info', {})
        info_text = (f"Имя: {user_info['name']}\n"
                     f"Компания: {user_info['company']}\n"
                     f"Должность: {user_info['position']}\n"
                     "Всё верно?")
        await message.answer(info_text, reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Да")],
                [types.KeyboardButton(text="Нет")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        ))
        await state.set_state(InfoCollectionStates.confirmation)
    except Exception as e:
        logger.error(f"Error in collect_position: {e}")
        await message.answer("Произошла ошибка при обработке информации о должности. Пожалуйста, попробуйте снова.")


async def collect_user_info(message: types.Message, state: FSMContext, key: str, next_question: Optional[str],
                            next_state):
    try:
        if not await validate_input(message):
            return
        await update_user_info(state, key, message.text)
        if next_question:
            await message.answer(next_question)
        await state.set_state(next_state)
    except Exception as e:
        await handle_error(message, f"Error in collect_{key}", e)


async def confirm_info(message: types.Message, state: FSMContext):
    try:
        if not await validate_input(message):
            return
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            current_level_id = (await state.get_data()).get('current_level_id')

            if message.text.lower() == "да":
                await save_user_info(message, state, repo)
                await message.answer("Информация сохранена.", reply_markup=types.ReplyKeyboardRemove())
                await message.answer(
                    "Нажмите 'Следующий вопрос' для продолжения или выберите действие из меню.",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[[types.KeyboardButton(text="Следующий вопрос")]],
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                )
                await state.set_state(QuizStates.intermediate)
                await update_user_state(repo, state, user.id)
                await repo.mark_level_completed(user.id, current_level_id)
            else:
                await start_info_collection_level(message, state, current_level_id, repo, user.id)
            await uow.commit()
    except Exception as e:
        await handle_error(message, "Error in confirm_info", e)


async def save_user_info(message: types.Message, state: FSMContext, repo: Repository):
    data = await state.get_data()
    user_info = data.get('user_info', {})
    user = await repo.get_user_by_chat_id(str(message.chat.id))

    user.first_name = user_info['name']
    user.company = user_info['company']
    user.position = user_info['position']


# Обновление информации пользователя в состоянии
async def update_user_info(state: FSMContext, key: str, value: str):
    data = await state.get_data()
    user_info = data.get('user_info', {})
    user_info[key] = value
    await state.update_data(user_info=user_info)


# Валидация входных данных
async def validate_input(message: types.Message) -> bool:
    if message.text.startswith('/'):
        await message.answer("Пожалуйста, завершите ввод данных перед использованием команды.")
        return False
    return True
