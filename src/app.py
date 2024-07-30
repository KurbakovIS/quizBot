from fastapi import FastAPI
from admin.admin import create_admin_app
from src.bot.bot import start_bot

app = FastAPI()

create_admin_app(app)

if __name__ == "__main__":
    import uvicorn
    import threading

    bot_thread = threading.Thread(target=start_bot)
    bot_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
