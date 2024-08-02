from fastapi import FastAPI
from passlib.context import CryptContext
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.requests import Request

from src.database.models import User, Product, Question, Admin as AdminModel, Level
from src.database.repository import Repository
from src.database.uow import UnitOfWork
from src.utils.settings import DATABASE_URL

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
engine = create_async_engine(DATABASE_URL)


class AdminAuthentication(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        async with UnitOfWork() as uow:
            repo = Repository(uow.session)
            admin = await repo.get_admin_by_username(username)
            if admin and pwd_context.verify(password, admin.password):
                request.session.update({"user": username})
                return True
        return False

    async def logout(self, request: Request) -> None:
        request.session.clear()

    async def authenticate(self, request: Request) -> bool:
        return "user" in request.session


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.chat_id, User.current_level, User.balance]
    form_columns = ["username", "chat_id", "current_level", "balance"]


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name, Product.price, Product.quantity]
    form_columns = ["name", "price", "quantity"]


class LevelAdmin(ModelView, model=Level):
    column_list = [Level.id, Level.name, Level.description, Level.intro_text, Level.questions, Level.image_file,
                   Level.number]
    form_columns = ["name", "description", "intro_text", "image_file", "number"]


class QuestionAdmin(ModelView, model=Question):
    column_list = [Question.id, Question.level, Question.text, Question.hint, Question.correct_answer,
                   Question.reward, Question.image_file]
    form_columns = ["level", "text", "hint", "correct_answer", "reward", "image_file"]


class AdminAdmin(ModelView, model=AdminModel):
    column_list = [AdminModel.id, AdminModel.username]
    form_columns = ["username", "password"]


def create_admin_app(app: FastAPI):
    admin_authentication = AdminAuthentication(secret_key="supersecretkey")
    admin = Admin(app, engine, authentication_backend=admin_authentication)
    admin.add_view(UserAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(QuestionAdmin)
    admin.add_view(LevelAdmin)
    admin.add_view(AdminAdmin)
    return admin
