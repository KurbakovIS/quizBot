from fastapi import FastAPI

from src.admin.admin import create_admin_app
app = FastAPI()

create_admin_app(app)
