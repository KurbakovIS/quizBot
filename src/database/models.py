import uuid

from passlib.context import CryptContext
from sqlalchemy import Integer, String, Boolean, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, mapped_column, Mapped

from src.database.custom_types import FileType
from src.database.entity import BaseEntity

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseEntity):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String, unique=True)
    chat_id: Mapped[str] = mapped_column(String, unique=True)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    current_level: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('levels.id'))
    completed_levels = relationship('Level', secondary='user_levels', back_populates='completed_users')
    skipped_levels = relationship('Level', secondary='user_skipped_levels', back_populates='skipped_users')
    stages_completed = relationship('StageCompletion', back_populates='user')
    balance: Mapped[float] = mapped_column(Float, default=0.0)

    company: Mapped[str] = mapped_column(String, nullable=True)
    position: Mapped[str] = mapped_column(String, nullable=True)


class Product(BaseEntity):
    __tablename__ = 'products'

    name: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer)


class Question(BaseEntity):
    __tablename__ = 'questions'

    level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('levels.id'))
    text: Mapped[str] = mapped_column(Text)
    hint: Mapped[str] = mapped_column(Text, nullable=True)
    correct_answer: Mapped[str] = mapped_column(Text)
    image_file: Mapped[str] = mapped_column(FileType(), nullable=True)
    level = relationship('Level', back_populates='questions')

    def __repr__(self):
        return self.text


class Level(BaseEntity):
    __tablename__ = 'levels'

    name: Mapped[str] = mapped_column(String)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    intro_text: Mapped[str] = mapped_column(Text)
    reward: Mapped[int] = mapped_column(Integer, nullable=True)
    is_intro: Mapped[bool] = mapped_column(Boolean, default=False)
    is_info_collection: Mapped[bool] = mapped_column(Boolean, default=False)
    is_object_recognition: Mapped[bool] = mapped_column(Boolean, default=False)
    image_file: Mapped[str] = mapped_column(FileType(), nullable=True)
    questions = relationship('Question', back_populates='level')
    completed_users = relationship('User', secondary='user_levels', back_populates='completed_levels')
    skipped_users = relationship('User', secondary='user_skipped_levels', back_populates='skipped_levels')

    def __repr__(self):
        return self.name


class UserLevel(BaseEntity):
    __tablename__ = 'user_levels'

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('levels.id'), primary_key=True)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'level_id', name='uq_user_levels_user_id_level_id'),
    )


class UserSkippedLevel(BaseEntity):
    __tablename__ = 'user_skipped_levels'

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True)
    level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('levels.id'), primary_key=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'level_id', name='uq_user_skipped_levels_user_id_level_id'),
    )


class StageCompletion(BaseEntity):
    __tablename__ = 'stage_completions'

    user_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey('users.id'))
    stage_id: Mapped[uuid.UUID] = mapped_column(UUID)
    used_hint: Mapped[bool] = mapped_column(Boolean, default=False)
    user = relationship('User', back_populates='stages_completed')

    __table_args__ = (
        UniqueConstraint('user_id', 'stage_id', name='uq_user_skipped_levels_user_id_stage_id'),
    )


class Admin(BaseEntity):
    __tablename__ = 'admins'

    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)

    def set_password(self, password):
        self.password = pwd_context.hash(password)


class UserState(BaseEntity):
    __tablename__ = 'user_states'

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))
    state: Mapped[str] = mapped_column(String, nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_states_user_id'),
    )
