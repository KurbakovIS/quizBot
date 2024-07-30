from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from passlib.context import CryptContext
from src.database.entity import BaseEntity

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseEntity):
    __tablename__ = 'users'
    username = mapped_column(String, unique=True)
    password = mapped_column(String)
    current_stage = mapped_column(Integer, default=0)
    stages_completed = relationship('StageCompletion', back_populates='user')


class Product(BaseEntity):
    __tablename__ = 'products'
    name = mapped_column(String)
    price = mapped_column(Integer)
    quantity = mapped_column(Integer)


class Question(BaseEntity):
    __tablename__ = 'questions'
    stage_id = mapped_column(UUID)
    text = mapped_column(String)
    hint = mapped_column(String)
    reward = mapped_column(Integer)


class StageCompletion(BaseEntity):
    __tablename__ = 'stage_completions'
    user_id = mapped_column(UUID, ForeignKey('users.id'))
    stage_id = mapped_column(UUID)
    used_hint = mapped_column(Boolean, default=False)
    user = relationship('User', back_populates='stages_completed')


class Admin(BaseEntity):
    __tablename__ = 'admins'
    username = mapped_column(String, unique=True)
    password = mapped_column(String)

    def set_password(self, password):
        self.password = pwd_context.hash(password)
