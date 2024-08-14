import os

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.cv import load_model, is_duck_present
from src.bot.gameplay.answer import skip_level
from src.bot.states import QuizStates
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def handle_object_recognition(message: types.Message, state: FSMContext, bot: Bot):
    file_path = None
    try:
        if message.text == "Пропустить уровень":
            await skip_level(message, state)
            return

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

        # Проверяем, что файл был успешно загружен
        if not os.path.exists(file_path):
            await message.answer("Ошибка загрузки изображения. Пожалуйста, попробуйте снова.")
            return

        # Теперь файл сохранен на сервере, и вы можете использовать его для обработки
        data = await state.get_data()
        level_id = data.get('current_level_id')

        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            level = await repo.get_level_by_id(level_id)

            reference_image_path = level.image_file  # Путь к эталонному изображению
            reward = level.reward  # Получаем количество очков из уровня

            # Проверяем, что эталонное изображение существует
            if not os.path.exists(reference_image_path):
                await message.answer("Ошибка загрузки эталонного изображения. Пожалуйста, попробуйте позже.")
                return

            model = load_model()

            # Проверяем наличие утки на изображении
            if is_duck_present(file_path, reference_image_path, model):
                await message.answer(f"Вы успешно нашли объект (утку) и заработали {reward} очков!")

                # Обновляем баланс пользователя
                if reward:
                    user = await repo.get_user_by_chat_id(str(message.chat.id))
                    await repo.update_user_balance(user.id, reward)
                    await uow.commit()

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
    finally:
        # Удаляем загруженный файл после завершения проверки
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

