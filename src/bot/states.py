from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    start = State()
    intro = State()
    question = State()
    intermediate = State()  # Промежуточное состояние между вопросами
    completed = State()
    info_collection = State()  # Новое состояние для сбора информаци
    object_recognition = State()
    return_to_skipped = State()  # Состояние для возврата к пропущенным уровням
    waiting_for_broadcast_message = State()  # Новое состояние для ввода сообщения для рассылки