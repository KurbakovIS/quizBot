from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert, update
from src.database import User, Question, Admin, Level


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_chat_id(self, chat_id: str):
        stmt = select(User).where(User.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, username: str, chat_id: str, first_name: str, last_name: str, current_level):
        stmt = insert(User).values(username=username, chat_id=chat_id, first_name=first_name, last_name=last_name,
                                   balance=0.0).returning(User)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()

    async def get_first_level(self):
        stmt = select(Level).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_first_question(self):
        stmt = select(Question).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_balance(self, user: User, amount: float):
        stmt = (
            update(User)
            .where(User.id == user.id)
            .values(balance=User.balance + amount)
            .returning(User)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_level_reward_and_messages(self, level_id: str):
        stmt = select(Level).where(Level.id == level_id)
        result = await self.session.execute(stmt)
        level = result.scalar_one_or_none()
        if level:
            return level.reward, level.correct_answer_message, level.incorrect_answer_text
        return 0, "Correct! You earned some points.", "Incorrect answer. Try again."

    async def get_admin_by_username(self, username: str):
        stmt = select(Admin).where(Admin.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_levels(self):
        stmt = select(Level)
        result = await self.session.execute(stmt)
        return result.scalars().all()