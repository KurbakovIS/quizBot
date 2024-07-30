from fastapi import FastAPI
from passlib.context import CryptContext
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from starlette.requests import Request

from src.database.models import User, Product, Question, Admin as AdminModel

DATABASE_URL = "postgresql+asyncpg://postgres:qwerty@localhost:5432/tg_quiz_bot"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)


class AdminAuthentication(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        async with SessionLocal() as session:
            query = await session.execute(
                text("SELECT * FROM admins WHERE username = :username"), {"username": username}
            )
            admin = query.fetchone()
            if admin and pwd_context.verify(password, admin.password):
                request.session.update({"user": username})
                return True
        return False

    async def logout(self, request: Request) -> None:
        request.session.clear()

    async def authenticate(self, request: Request) -> bool:
        return "user" in request.session


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.current_stage]


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name, Product.price, Product.quantity]


class QuestionAdmin(ModelView, model=Question):
    column_list = [Question.id, Question.stage_id, Question.text, Question.hint, Question.reward]


class AdminAdmin(ModelView, model=AdminModel):
    column_list = [AdminModel.id, AdminModel.username]


def create_admin_app(app: FastAPI):
    admin_authentication = AdminAuthentication(secret_key="supersecretkey")
    admin = Admin(app, engine, authentication_backend=admin_authentication)
    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(AdminAdmin)
    return admin
