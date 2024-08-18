import os

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.cv import load_model, is_duck_present
from src.bot.gameplay.answer import skip_level
from src.bot.states import QuizStates
from src.bot.utils.state_management import update_user_state
from src.database.repository import Repository
from src.database.uow import UnitOfWork


def create_skip_level_keyboard() -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="Пропустить уровень")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


async def handle_object_recognition(message: types.Message, state: FSMContext, bot: Bot):
    if message.text == "Пропустить уровень":
        await process_skip_level(message, state)
        return

    if not message.photo:
        await message.answer(
            "Пожалуйста, загрузите изображение.",
            reply_markup=create_skip_level_keyboard()
        )
        return

    await message.answer("Проверка изображения началась, пожалуйста, подождите...")

    file_path = await download_user_photo(message, bot)
    if not file_path:
        await message.answer(
            "Ошибка загрузки изображения. Пожалуйста, попробуйте снова.",
            reply_markup=create_skip_level_keyboard()
        )
        return

    try:
        await process_image_recognition(file_path, message, state)
    except Exception as e:
        logger.error(f"Error in handle_object_recognition: {e}")
        await message.answer(
            "Произошла ошибка при обработке изображения. Пожалуйста, попробуйте позже.",
            reply_markup=create_skip_level_keyboard()
        )
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


async def process_skip_level(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        await skip_level(message, state, repo)
        await uow.commit()


async def download_user_photo(message: types.Message, bot: Bot) -> str | None:
    user_photo = message.photo[-1]
    file_info = await bot.get_file(user_photo.file_id)
    file_path = f"user_photo_{message.from_user.id}.jpg"

    await bot.download_file(file_info.file_path, file_path)

    if not os.path.exists(file_path):
        logger.error(f"Failed to download file: {file_path}")
        return None

    return file_path


async def process_image_recognition(file_path: str, message: types.Message, state: FSMContext):
    data = await state.get_data()
    level_id = data.get('current_level_id')

    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        level = await repo.get_level_by_id(level_id)
        user = await repo.get_user_by_chat_id(str(message.chat.id))

        reference_image_path = level.image_file
        reward = level.reward

        if not os.path.exists(reference_image_path):
            await message.answer(
                "Ошибка загрузки эталонного изображения. Пожалуйста, попробуйте позже.",
                reply_markup=create_skip_level_keyboard()
            )
            return

        model = load_model()

        if is_duck_present(file_path, reference_image_path, model):
            await handle_successful_recognition(message, state, repo, user, reward)
            await repo.mark_level_completed(user.id, level.id)
            await uow.commit()
        else:
            await message.answer(
                "Утка не найдена на изображении. Попробуйте снова.",
                reply_markup=create_skip_level_keyboard()
            )


async def handle_successful_recognition(message: types.Message, state: FSMContext, repo, user, reward: int):
    await message.answer(f"Верно! Вы заработали {reward} points.")

    if reward:
        await repo.update_user_balance(user.id, reward)

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
