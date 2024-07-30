from io import BytesIO

import pandas as pd
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi_admin.app import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider
from fastapi_admin.resources import Model, Field
from fastapi_admin.template import templates
from fastapi_admin.widgets import displays, inputs
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.database.models import User, Question, Product
from src.database.session import get_db, SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin_app(app: FastAPI):
    @app.on_event("startup")
    async def startup():
        admin_app.configure(
            templates=templates,
            session_maker=SessionLocal,
            admin_secret="your-secret-key",
            providers=[
                UsernamePasswordProvider(
                    admin_model=User,
                    login_logo_url="https://your-logo-url.com",
                    pwd_context=pwd_context,
                )
            ],
        )

        class UserResource(Model):
            label = "Users"
            model = User
            page_pre_title = "User Management"
            page_title = "Users"
            icon = "fa fa-user"
            filters = [
                inputs.Search(label="Search", name="username"),
            ]
            fields = [
                Field(name="id", display=displays.Input(display=displays.Text())),
                Field(name="username", display=displays.Input(display=displays.Text())),
                Field(name="password", display=displays.Input(display=displays.Password())),
                Field(name="current_stage", display=displays.Input(display=displays.Number())),
            ]

            async def save(self, request, obj, data, create, session):
                if "password" in data:
                    data["password"] = pwd_context.hash(data["password"])
                await super().save(request, obj, data, create, session)

        class ProductResource(Model):
            label = "Products"
            model = Product
            page_pre_title = "Product Management"
            page_title = "Products"
            icon = "fa fa-box"
            fields = [
                "id",
                "name",
                "price",
                "quantity",
            ]

        class QuestionResource(Model):
            label = "Questions"
            model = Question
            page_pre_title = "Question Management"
            page_title = "Questions"
            icon = "fa fa-question"
            fields = [
                "id",
                "stage_id",
                "text",
                "hint",
                "reward",
            ]

        admin_app.register(UserResource)
        admin_app.register(ProductResource)
        admin_app.register(QuestionResource)

    @app.get("/export_users")
    async def export_users(db: Session = Depends(get_db)):
        users = db.query(User).all()
        user_data = [{"id": user.id, "username": user.username, "current_stage": user.current_stage} for user in users]
        df = pd.DataFrame(user_data)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Users")
        output.seek(0)
        return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                 headers={"Content-Disposition": "attachment;filename=users.xlsx"})

    app.mount("/admin", admin_app, name="admin")
