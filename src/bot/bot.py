import asyncio
from loguru import logger

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from src.database.repository import Repository
from src.database.uow import UnitOfWork

API_TOKEN = '6939810787:AAFU363xcu1aVMUlbVcLMH_Awidr3R9RdR8'

logger.add("bot.log", rotation="100 MB")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class QuizStates(StatesGroup):
    start = State()


@dp.message(Command('start'))
async def send_welcome(message: types.Message):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        user = await repo.get_user_by_chat_id(str(message.chat.id))
        if not user:
            await repo.create_user(
                username=message.from_user.username,
                chat_id=str(message.chat.id),
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )

        level = await repo.get_first_level()
        welcome_text = level.intro_text if level else "Добро пожаловать в игру!"
        await message.answer(welcome_text)


@dp.message(Command('next'))
async def send_next_message(message: types.Message):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        question = await repo.get_first_question()
        if question:
            await message.answer(question.text)
        else:
            await message.answer("Больше вопросов нет.")


@dp.message()
async def handle_answer(message: types.Message):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        question = await repo.get_first_question()

        if question and message.text.lower() == question.correct_answer.lower():
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            level = await repo.get_first_level()
            reward, correct_message, incorrect_message = await repo.get_level_reward_and_messages(level.id)
            await repo.update_user_balance(user, reward)
            await message.answer(f"{correct_message} Вы заработали {reward} points.")
        else:
            level = await repo.get_first_level()
            _, _, incorrect_message = await repo.get_level_reward_and_messages(level.id)
            await message.answer(incorrect_message)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger.info("Starting bot")
    asyncio.run(main())
