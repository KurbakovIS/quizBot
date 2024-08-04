import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User, Product, Question, Level


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_chat_id(self, chat_id: str):
        result = await self.session.execute(select(User).where(User.chat_id == chat_id))
        return result.scalar_one_or_none()

    async def create_user(self, username: str, chat_id: str, first_name: str, last_name: str, current_level: str):
        new_user = User(
            username=username,
            chat_id=chat_id,
            first_name=first_name,
            last_name=last_name,
            current_level=current_level,
            balance=0,
            stages_completed=[]
        )
        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def get_first_level(self):
        result = await self.session.execute(select(Level).order_by(Level.number.asc()).limit(1))
        return result.scalar_one_or_none()

    async def get_questions_by_level(self, level_id: uuid.UUID):
        result = await self.session.execute(select(Question).where(Question.level_id == level_id))
        return result.scalars().all()

    async def get_question_by_id(self, question_id: uuid.UUID):
        result = await self.session.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def get_next_level(self, current_level_number: int):
        result = await self.session.execute(
            select(Level).where(Level.number > current_level_number).order_by(Level.number.asc()).limit(1))
        return result.scalar_one_or_none()

    async def update_user_balance(self, user: User, reward: int):
        user.balance += reward
        self.session.add(user)
        await self.session.commit()

    async def get_level_reward_and_messages(self, level_id: uuid.UUID):
        result = await self.session.execute(select(Level).where(Level.id == level_id))
        level = result.scalar_one_or_none()
        if level:
            return level.reward, level.correct_answer_message, level.incorrect_answer_text
        return None, None, None

    async def get_incorrect_message(self, level_id: uuid.UUID):
        result = await self.session.execute(select(Level.incorrect_answer_text).where(Level.id == level_id))
        return result.scalar_one_or_none()

    async def update_user_level(self, user: User, level_id: uuid.UUID):
        user.current_level = level_id
        self.session.add(user)
        await self.session.commit()

    async def mark_level_completed(self, user: User, level_id: uuid.UUID):
        user.stages_completed.append({"level_id": str(level_id), "completed": True})
        self.session.add(user)
        await self.session.commit()
