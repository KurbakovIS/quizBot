from aiogram import types
from aiogram.fsm.context import FSMContext
import asyncio
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from src.bot.states import QuizStates  # Импортируем состояния


# Команда /broadcast для начала процесса рассылки
async def handle_broadcast(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        user = await repo.get_user_by_chat_id(str(user_id))

        if not user or not user.admin:
            await message.answer("У вас нет прав для использования этой команды.")
            return

        current_state = await state.get_state()
        await state.update_data(previous_state=current_state)

        await message.answer("Пожалуйста, введите сообщение для рассылки.")
        await state.set_state(QuizStates.waiting_for_broadcast_message)  # Переводим в состояние ожидания сообщения


# Обработчик для ввода сообщения
async def handle_broadcast_message(message: types.Message, state: FSMContext):
    broadcast_message = message.text.strip()

    if not broadcast_message:
        await message.answer("Сообщение не может быть пустым. Попробуйте снова.")
        return

    await message.answer("Начинается отправка сообщений, пожалуйста, подождите...")

    asyncio.create_task(send_broadcast_to_all_users(broadcast_message, message.bot))

    # Отправляем сообщение об успешной отправке
    await message.answer("Сообщение успешно отправлено всем пользователям.")

    data = await state.get_data()
    previous_state = data.get('previous_state')

    if previous_state:
        await state.set_state(previous_state)
    else:
        await state.clear()


# Функция для отправки сообщений всем пользователям
async def send_broadcast_to_all_users(broadcast_message: str, bot):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            users = await repo.get_all_users()

            for u in users:
                if u.chat_id:
                    try:
                        await bot.send_message(chat_id=u.chat_id, text=broadcast_message)
                    except Exception as e:
                        print(f"Не удалось отправить сообщение пользователю {u.chat_id}: {e}")
    except Exception as e:
        print(f"Ошибка при отправке сообщений: {e}")
