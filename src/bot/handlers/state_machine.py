from aiogram import types
from aiogram.fsm.context import FSMContext
from loguru import logger

from src.bot.handlers.answer import complete_quiz, start_info_collection_level, start_object_recognition_level
from src.bot.handlers.game import start_game
from src.bot.state_machine import InfoCollectionStates
from src.bot.utils.skip_message import skip_command
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def collect_name(message: types.Message, state: FSMContext):
    try:
        if message.text.startswith('/'):
            await message.answer("Пожалуйста, завершите ввод данных перед использованием команды.")
            return  # Прерываем выполнение, чтобы остановить переход к следующему этапу

        data = await state.get_data()  # Получаем все данные из состояния
        user_info = data.get('user_info', {})
        user_info['name'] = message.text
        await state.update_data(user_info=user_info)
        await message.answer("В какой компании ты работаешь?")
        await state.set_state(InfoCollectionStates.collecting_company)
    except Exception as e:
        logger.error(f"Error in collect_name: {e}")
        await message.answer("Произошла ошибка при обработке вашего имени. Пожалуйста, попробуйте снова.")


async def collect_company(message: types.Message, state: FSMContext):
    try:
        if message.text.startswith('/'):
            await message.answer("Пожалуйста, завершите ввод данных перед использованием команды.")
            return  # Прерываем выполнение, чтобы остановить переход к следующему этапу

        data = await state.get_data()  # Получаем все данные из состояния
        user_info = data.get('user_info', {})
        user_info['company'] = message.text
        await state.update_data(user_info=user_info)
        await message.answer("Какая у тебя должность?")
        await state.set_state(InfoCollectionStates.collecting_position)
    except Exception as e:
        logger.error(f"Error in collect_company: {e}")
        await message.answer("Произошла ошибка при обработке информации о компании. Пожалуйста, попробуйте снова.")


async def collect_position(message: types.Message, state: FSMContext):
    try:
        if message.text.startswith('/'):
            await message.answer("Пожалуйста, завершите ввод данных перед использованием команды.")
            return  # Прерываем выполнение, чтобы остановить переход к следующему этапу

        data = await state.get_data()  # Получаем все данные из состояния
        user_info = data.get('user_info', {})
        user_info['position'] = message.text
        await state.update_data(user_info=user_info)

        # Подтверждение информации
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


async def confirm_info(message: types.Message, state: FSMContext):
    try:
        if message.text.startswith('/'):
            await message.answer("Пожалуйста, завершите ввод данных перед использованием команды.")
            return  # Прерываем выполнение, чтобы остановить переход к следующему этапу

        if message.text.lower() == "да":
            async with UnitOfWork() as uow:
                repo = Repository(uow.session)
                data = await state.get_data()
                user_info = data.get('user_info', {})
                user = await repo.get_user_by_chat_id(str(message.chat.id))

                # Сохранение данных в модель User
                user.first_name = user_info['name']
                user.company = user_info['company']
                user.position = user_info['position']

                # Сохраняем изменения
                await uow.commit()

            await message.answer("Информация сохранена.", reply_markup=types.ReplyKeyboardRemove())

            # Переход к следующему уровню
            async with UnitOfWork() as uow:
                repo = Repository(uow.session)
                current_level_id = data.get('current_level_id')
                next_level = await repo.get_next_level(current_level_id)

                if next_level:
                    await state.update_data(current_level_id=next_level.id)

                    # Проверка типа следующего уровня
                    if next_level.is_object_recognition:
                        await start_object_recognition_level(message, state,  next_level)
                    elif next_level.is_info_collection:
                        await start_info_collection_level(message, state, repo, next_level)
                    else:
                        await start_game(message, state)
                else:
                    await complete_quiz(message, state)
        else:
            # Начинаем сбор информации заново
            async with UnitOfWork() as uow:
                repo = Repository(uow.session)
                current_level_id = (await state.get_data()).get('current_level_id')
                level = await repo.get_level_by_id(current_level_id)
                await start_info_collection_level(message, state, repo, level)
    except Exception as e:
        logger.error(f"Error in confirm_info: {e}")
        await message.answer("Произошла ошибка при сохранении информации. Пожалуйста, попробуйте позже.")
