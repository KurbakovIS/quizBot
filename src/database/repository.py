import uuid

from loguru import logger
from sqlalchemy import insert, update, select, delete, exists
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, Question, Level, StageCompletion, UserLevel, UserState, Admin, UserSkippedLevel, \
    Product, UserProduct


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

    async def get_first_level(self) -> Level:
        result = await self.session.execute(select(Level).order_by(Level.number.asc()).limit(1))
        return result.scalar_one_or_none()

    async def get_questions_by_level(self, level_id: uuid.UUID):
        result = await self.session.execute(select(Question).where(Question.level_id == level_id))
        return result.scalars().all()

    async def get_question_by_id(self, question_id: uuid.UUID):
        result = await self.session.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def get_next_level(self, current_level_id: uuid.UUID, user_id: uuid.UUID) -> Level:
        current_level = await self.get_level_by_id(current_level_id)
        result = await self.session.execute(
            select(Level)
            .where(Level.number > current_level.number)
            .where(~Level.id.in_(select(StageCompletion.stage_id).where(StageCompletion.user_id == user_id)))
            .where(~Level.id.in_(select(UserSkippedLevel.level_id).where(UserSkippedLevel.user_id == user_id)))
            .order_by(Level.number.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_level_by_id(self, level_id: uuid.UUID) -> Level:
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
        user_skipped_level = await self.get_exist_skipped_by_level_id(level_id)
        if user_skipped_level:
            logger.info(f"Level {level_id} was skipped by user {user_id}. Skipping UserLevel addition.")
            return
        stmt = insert(UserLevel).values(user_id=user_id, level_id=level_id)
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

    async def mark_level_skipped(self, user_id, level_id):
        # Логика для записи пропущенного уровня
        skipped_level = UserSkippedLevel(user_id=user_id, level_id=level_id)
        self.session.add(skipped_level)

    async def get_exist_skipped_by_level_id(self, level_id: uuid.UUID) -> bool:
        # Подзапрос на проверку существования записи с данным level_id
        stmt = select(exists().where(UserSkippedLevel.level_id == level_id))

        # Выполнение запроса
        result = await self.session.execute(stmt)
        return result.scalar()

    async def get_skipped_levels(self, user_id):
        result = await self.session.execute(
            select(Level).join(UserSkippedLevel).where(UserSkippedLevel.user_id == user_id)
        )
        return result.scalars().all()

    async def get_skipped_level_by_name(self, user_id, level_name):
        result = await self.session.execute(
            select(Level).join(UserSkippedLevel)
            .where(UserSkippedLevel.user_id == user_id, Level.name == level_name)
        )
        return result.scalar_one_or_none()

    async def remove_skipped_level(self, user_id: uuid.UUID, level_id: uuid.UUID):
        await self.session.execute(
            delete(UserSkippedLevel)
            .where(UserSkippedLevel.user_id == user_id)
            .where(UserSkippedLevel.level_id == level_id)
        )

    async def get_completed_levels(self, user_id):
        result = await self.session.execute(
            select(StageCompletion.stage_id)
            .where(StageCompletion.user_id == user_id)
        )
        return {row for row in result.scalars().all()}

    async def get_available_products(self):
        result = await self.session.execute(select(Product).where(Product.quantity > 0))
        return result.scalars().all()

    async def purchase_product(self, user_id: uuid.UUID, product_id: uuid.UUID):
        # Уменьшаем количество продукта на 1
        await self.session.execute(
            update(Product)
            .where(Product.id == product_id)
            .where(Product.quantity > 0)
            .values(quantity=Product.quantity - 1)
        )

        # Проверяем, покупал ли пользователь этот товар ранее
        result = await self.session.execute(
            select(UserProduct).where(UserProduct.user_id == user_id, UserProduct.product_id == product_id)
        )
        existing_entry = result.scalar_one_or_none()

        if existing_entry:
            # Если пользователь уже покупал этот товар, увеличиваем количество
            update_stmt = (
                update(UserProduct)
                .where(UserProduct.user_id == user_id)
                .where(UserProduct.product_id == product_id)
                .values(quantity=UserProduct.quantity + 1)
            )
            await self.session.execute(update_stmt)
        else:
            # Если пользователь покупает товар впервые, создаем новую запись
            insert_stmt = (
                insert(UserProduct)
                .values(user_id=user_id, product_id=product_id, quantity=1)
            )
            await self.session.execute(insert_stmt)

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product:
        result = await self.session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()
