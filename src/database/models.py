import uuid

from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID
from passlib.context import CryptContext
from src.database.entity import BaseEntity

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseEntity):
    __tablename__ = 'users'
    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    current_stage: Mapped[int] = mapped_column(Integer, default=0)
    stages_completed = relationship('StageCompletion', back_populates='user')


class Product(BaseEntity):
    __tablename__ = 'products'
    name: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)


class Question(BaseEntity):
    __tablename__ = 'questions'
    stage_id: Mapped[uuid.UUID] = mapped_column(UUID)
    text: Mapped[str] = mapped_column(String)
    hint: Mapped[str] = mapped_column(String)
    reward: Mapped[int] = mapped_column(Integer)


class StageCompletion(BaseEntity):
    __tablename__ = 'stage_completions'
    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey('users.id'))
    stage_id: Mapped[uuid.UUID] = mapped_column(UUID)
    used_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    user = relationship('User', back_populates='stages_completed')


class Admin(BaseEntity):
    __tablename__ = 'admins'
    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)

    def set_password(self, password):
        self.password = pwd_context.hash(password)
