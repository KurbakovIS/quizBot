from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.cv import load_model, is_duck_present
from src.bot.handlers.answer import complete_quiz
from src.bot.handlers.game import start_game
from src.bot.states import QuizStates
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def handle_object_recognition(message: types.Message, state: FSMContext, bot: Bot):
    try:
        if not message.photo:
            await message.answer("Пожалуйста, загрузите изображение.")
            return
        # Сообщаем пользователю, что проверка началась
        await message.answer("Проверка изображения началась, пожалуйста, подождите...")

        user_photo = message.photo[-1]  # Получаем фото наивысшего качества
        file_info = await bot.get_file(user_photo.file_id)
        file_path = f"user_photo_{message.from_user.id}.jpg"

        # Скачиваем и сохраняем файл
        await bot.download_file(file_info.file_path, file_path)

        # Теперь файл сохранен на сервере, и вы можете использовать его для обработки
        data = await state.get_data()
        level_id = data.get('current_level_id')

        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            level = await repo.get_level_by_id(level_id)

            reference_image_path = level.image_file  # Путь к эталонному изображению

            model = load_model()
            if is_duck_present(file_path, reference_image_path, model):
                await message.answer("Вы успешно нашли объект (утку).")

                # Переход в состояние intermediate после успешного завершения уровня
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
                await message.answer("Утка не найдена на изображении. Попробуйте снова.")

    except Exception as e:
        logger.error(f"Error in handle_object_recognition: {e}")
        await message.answer("Произошла ошибка при обработке изображения. Пожалуйста, попробуйте позже.")
