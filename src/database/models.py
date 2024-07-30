from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, registry, mapped_column

mapper_registry = registry()


@mapper_registry.mapped
class User:
    __tablename__ = 'users'
    id = mapped_column(Integer, primary_key=True)
    username = mapped_column(String, unique=True)
    password = mapped_column(String)
    current_stage = mapped_column(Integer, default=0)
    stages_completed = relationship('StageCompletion', back_populates='user')


@mapper_registry.mapped
class Product:
    __tablename__ = 'products'
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String)
    price = mapped_column(Integer)
    quantity = mapped_column(Integer)


@mapper_registry.mapped
class Question:
    __tablename__ = 'questions'
    id = mapped_column(Integer, primary_key=True)
    stage_id = mapped_column(Integer)
    text = mapped_column(String)
    hint = mapped_column(String)
    reward = mapped_column(Integer)


@mapper_registry.mapped
class StageCompletion:
    __tablename__ = 'stage_completions'
    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(Integer, ForeignKey('users.id'))
    stage_id = mapped_column(Integer)
    used_hint = mapped_column(Boolean, default=False)
    user = relationship('User', back_populates='stages_completed')
