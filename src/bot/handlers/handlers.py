from aiogram import Router, F
from aiogram.filters.state import StateFilter

from src.bot.handlers.answer import handle_answer
from src.bot.handlers.game import start_game
from src.bot.handlers.intro import continue_intro
from src.bot.start import start_bot
from src.bot.states import QuizStates
from aiogram.filters import CommandStart

router = Router()

# Регистрация обработчика команды /start
router.message.register(start_bot, CommandStart())

# Регистрация обработчика текстового события "Далее" в состоянии QuizStates.intro
router.message.register(continue_intro, StateFilter(QuizStates.intro), F.text == "Далее")

# Регистрация обработчика текстового события "Далее" в состоянии QuizStates.start
router.message.register(start_game, StateFilter(QuizStates.start), F.text == "Далее")

# Регистрация обработчика ответов на вопросы в состоянии QuizStates.question
router.message.register(handle_answer, StateFilter(QuizStates.question))
