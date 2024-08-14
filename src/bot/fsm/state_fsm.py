from aiogram.fsm.state import StatesGroup, State


class InfoCollectionStates(StatesGroup):
    collecting_name = State()
    collecting_company = State()
    collecting_position = State()
    confirmation = State()
