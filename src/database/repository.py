import uuid
from sqlalchemy import insert, update, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User, Question, Level, StageCompletion, UserLevel, UserState, Admin


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_chat_id(self, chat_id: str):
        result = await self.session.execute(select(User).where(User.chat_id == chat_id))
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str):
        result = await self.session.execute(select(Admin).where(Admin.username == username))
        return result.scalar_one_or_none()

    async def create_user(self, username: str, chat_id: str, first_name: str, last_name: str, current_level: uuid.UUID):
        stmt = insert(User).values(
            username=username,
            chat_id=chat_id,
            first_name=first_name,
            last_name=last_name,
            current_level=current_level,
            balance=0
        ).returning(User)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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

    async def update_user_balance(self, user_id: uuid.UUID, reward: int):
        stmt = update(User).where(User.id == user_id).values(balance=User.balance + reward)
        await self.session.execute(stmt)

    async def get_level_reward(self, level_id: uuid.UUID):
        result = await self.session.execute(select(Level.reward).where(Level.id == level_id))
        return result.scalar_one_or_none()

    async def update_user_level(self, user_id: uuid.UUID, level_id: uuid.UUID):
        stmt = update(User).where(User.id == user_id).values(current_level=level_id)
        await self.session.execute(stmt)

    async def mark_level_completed(self, user_id: uuid.UUID, level_id: uuid.UUID):
        stmt = insert(StageCompletion).values(user_id=user_id, stage_id=level_id)
        await self.session.execute(stmt)

    async def add_user_level_entry(self, user_id: uuid.UUID, level_id: uuid.UUID):
        stmt = insert(UserLevel).values(user_id=user_id, level_id=level_id)
        await self.session.execute(stmt)

    async def add_stage_completion(self, user_id: uuid.UUID, stage_id: uuid.UUID):
        stmt = insert(StageCompletion).values(user_id=user_id, stage_id=stage_id)
        await self.session.execute(stmt)

    async def get_user_state(self, user_id: uuid.UUID):
        result = await self.session.execute(select(UserState).where(UserState.user_id == user_id))
        return result.scalar_one_or_none()

    async def update_user_state(self, user_id: uuid.UUID, state: str, data: dict):
        # Преобразование UUID в строку
        data = {key: (str(value) if isinstance(value, uuid.UUID) else value) for key, value in data.items()}
        stmt = pg_insert(UserState).values(user_id=user_id, state=state, data=data).on_conflict_do_update(
            index_elements=['user_id'],
            set_=dict(state=state, data=data)
        )
        await self.session.execute(stmt)
