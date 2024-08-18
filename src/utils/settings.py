import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:qwerty@localhost:5432/tg_quiz_bot")
API_TOKEN = os.getenv("API_TOKEN", "7541370135:AAG1Bt124QEXuaNm1p-hajNEPyeGs0zue4A")
