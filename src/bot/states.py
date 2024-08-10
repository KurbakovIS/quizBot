from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    start = State()
    intro = State()
    question = State()
    intermediate = State()  # Промежуточное состояние между вопросами
    completed = State()