from aiogram import Router, F
from aiogram.filters.state import StateFilter
from src.bot.handlers.answer import handle_answer
from src.bot.handlers.game import start_game
from src.bot.handlers.intro import continue_intro
from src.bot.start import start_bot
from src.bot.states import QuizStates
from aiogram.filters import CommandStart

router = Router()


def register_start_handlers(router: Router):
    router.message.register(start_bot, CommandStart())


def register_intro_handlers(router: Router):
    router.message.register(continue_intro, StateFilter(QuizStates.intro), F.text == "Далее")


def register_game_handlers(router: Router):
    router.message.register(start_game, StateFilter(QuizStates.start), F.text == "Далее")


def register_answer_handlers(router: Router):
    router.message.register(handle_answer, StateFilter(QuizStates.question))


def register_hint_handlers(router: Router):
    router.message.register(handle_answer, StateFilter(QuizStates.question), F.text == "Подсказка")


def register_all_handlers(router: Router):
    register_start_handlers(router)
    register_intro_handlers(router)
    register_game_handlers(router)
    register_answer_handlers(router)
    register_hint_handlers(router)


register_all_handlers(router)
