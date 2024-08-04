import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User, Question, Level, StageCompletion, UserLevel

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
            balance=0
        )
        self.session.add(new_user)
        await self.session.flush()  # Обеспечиваем, что новый пользователь будет иметь ID перед коммитом
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

    async def get_next_level(self, current_level_id: uuid.UUID):
        current_level = await self.get_level_by_id(current_level_id)
        result = await self.session.execute(
            select(Level).where(Level.number > current_level.number).order_by(Level.number.asc()).limit(1))
        return result.scalar_one_or_none()

    async def get_level_by_id(self, level_id: uuid.UUID):
        result = await self.session.execute(select(Level).where(Level.id == level_id))
        return result.scalar_one_or_none()

    async def update_user_balance(self, user: User, reward: int):
        user.balance += reward
        self.session.add(user)

    async def get_level_reward(self, level_id: uuid.UUID):
        result = await self.session.execute(select(Level.reward).where(Level.id == level_id))
        return result.scalar_one_or_none()

    async def update_user_level(self, user: User, level_id: uuid.UUID):
        user.current_level = level_id
        self.session.add(user)

    async def mark_level_completed(self, user: User, level_id: uuid.UUID):
        user.stages_completed.append({"level_id": str(level_id), "completed": True})
        self.session.add(user)

    async def add_user_level_entry(self, user_id: uuid.UUID, level_id: uuid.UUID):
        new_entry = UserLevel(user_id=user_id, level_id=level_id)
        self.session.add(new_entry)

    async def add_stage_completion(self, user_id: uuid.UUID, stage_id: uuid.UUID):
        new_completion = StageCompletion(user_id=user_id, stage_id=stage_id)
        self.session.add(new_completion)
