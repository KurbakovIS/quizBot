import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from src.database.models import User
from src.database.session import SessionLocal

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class QuizStates(StatesGroup):
    start = State()


# Получение сессии базы данных
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    await message.answer("Welcome to the Quiz Bot!")


@dp.message(Command('quiz'))
async def start_quiz(message: types.Message, state: FSMContext):
    db = next(get_db_session())
    user = db.query(User).filter(User.username == message.from_user.username).first()
    if not user:
        user = User(username=message.from_user.username)
        db.add(user)
        db.commit()
    await message.answer("Quiz started!")
    await state.set_state(QuizStates.start)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
