import uuid

from aiogram import types
from loguru import logger
from aiogram.fsm.context import FSMContext

from src.bot.common import handle_common_error
from src.bot.start import start_bot
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def handle_error(message: types.Message, exception: Exception):
    logger.error(f"Error: {exception}")
    await message.answer("Произошла ошибка при обработке команды. Пожалуйста, попробуйте позже.")


async def handle_menu_start(message: types.Message, state: FSMContext):
    try:
        await start_bot(message, state)
    except Exception as e:
        await handle_error(message, e)


async def handle_hide_menu(message: types.Message):
    try:
        await message.answer("Меню скрыто. Вы можете снова открыть его, отправив /start.",
                             reply_markup=types.ReplyKeyboardRemove())
    except Exception as e:
        await handle_error(message, e)


async def handle_comment(message: types.Message):
    try:
        await message.answer("Спасибо за ваш отзыв! Пожалуйста, оставьте его в ответ на это сообщение.")
    except Exception as e:
        await handle_error(message, e)


async def handle_demo(message: types.Message):
    try:
        await message.answer(
            "Чтобы записаться на демо, пожалуйста, заполните форму по следующей ссылке: [ссылка на форму]")
    except Exception as e:
        await handle_error(message, e)


async def handle_shop(message: types.Message, state: FSMContext):
    try:
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            products = await repo.get_available_products()

            if not products:
                await message.answer("К сожалению, все товары распроданы.")
                return

            buttons = [
                [types.InlineKeyboardButton(text=f"{product.name} - {product.price} points.",
                                            callback_data=str(product.id))]
                for product in products
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)

            await message.answer("Выберите товар:", reply_markup=keyboard)
    except Exception as e:
        await handle_common_error(message, "Error in handle_shop", e)


async def handle_purchase(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        product_id = uuid.UUID(callback_query.data)
        product_name = ""
        product_price = 0.0
        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            user = await repo.get_user_by_chat_id(str(callback_query.from_user.id))

            product = await repo.get_product_by_id(product_id)
            if not product or product.quantity <= 0:
                await callback_query.message.answer("Этот товар уже распродан.")
                return

            if user.balance < product.price:
                await callback_query.message.answer("У вас недостаточно средств для покупки.")
                return

            # Обновляем данные в базе
            await repo.purchase_product(user.id, product.id)
            await repo.update_user_balance(user.id, -product.price)

            # Сохраняем информацию о покупке для использования после выхода из контекста UoW
            product_name = product.name
            product_price = product.price

            await uow.commit()

        await callback_query.message.answer(f"Вы успешно купили {product_name} за {product_price} points.")
    except Exception as e:
        await handle_common_error(callback_query.message, "Error in handle_purchase", e)


async def handle_info(message: types.Message):
    try:
        await message.answer(
            "Test IT - это платформа для тестирования ваших знаний в области информационных технологий. "
            "Мы предлагаем разнообразные викторины и тесты, чтобы помочь вам улучшить свои навыки.")
    except Exception as e:
        await handle_error(message, e)


async def handle_subscribe(message: types.Message):
    try:
        await message.answer(
            "Чтобы подписаться на Test IT, пожалуйста, посетите следующую ссылку: [ссылка на подписку]")
    except Exception as e:
        await handle_error(message, e)
