from aiogram import types


def get_main_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Старт")],
            [types.KeyboardButton(text="Узнать о Test IT")],
            [types.KeyboardButton(text="Оставить отзыв")],
            [types.KeyboardButton(text="Записаться на демо")],
            [types.KeyboardButton(text="Магазин мерча")],
            [types.KeyboardButton(text="Подписаться на Test IT")],
        ],
        resize_keyboard=True
    )
