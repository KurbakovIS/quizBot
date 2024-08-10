from aiogram import Router, F
from aiogram.filters.state import StateFilter
from src.bot.handlers.answer import handle_answer
from src.bot.handlers.game import start_game
from src.bot.handlers.menu.comment import handle_comment
from src.bot.handlers.menu.demo import handle_demo
from src.bot.handlers.menu.handle_next_question import handle_next_question
from src.bot.handlers.menu.info import handle_info
from src.bot.handlers.intro import continue_intro
from src.bot.handlers.menu.menu_start import handle_menu_start
from src.bot.handlers.menu.shop import handle_shop
from src.bot.handlers.menu.subscribe import handle_subscribe
from src.bot.start import start_bot
from src.bot.states import QuizStates
from aiogram.filters import CommandStart, Command

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


def register_menu_handlers(router: Router):
    # Обработчики команд
    router.message.register(handle_info, Command("info"), StateFilter(QuizStates.intermediate, QuizStates.completed))
    router.message.register(handle_comment, Command("comment"),
                            StateFilter(QuizStates.intermediate, QuizStates.completed))
    router.message.register(handle_demo, Command("demo"), StateFilter(QuizStates.intermediate, QuizStates.completed))
    router.message.register(handle_shop, Command("shop"), StateFilter(QuizStates.intermediate, QuizStates.completed))
    router.message.register(handle_subscribe, Command("subscribe"),
                            StateFilter(QuizStates.intermediate, QuizStates.completed))
    router.message.register(handle_menu_start, Command("start"),
                            StateFilter(QuizStates.intermediate, QuizStates.completed))
    # Обработчики текстовых кнопок
    router.message.register(handle_info, F.text == "Узнать о Test IT", StateFilter(QuizStates.intermediate))
    router.message.register(handle_comment, F.text == "Оставить отзыв", StateFilter(QuizStates.intermediate))
    router.message.register(handle_demo, F.text == "Записаться на демо", StateFilter(QuizStates.intermediate))
    router.message.register(handle_shop, F.text == "Магазин мерча", StateFilter(QuizStates.intermediate))
    router.message.register(handle_subscribe, F.text == "Подписаться на Test IT", StateFilter(QuizStates.intermediate))
    router.message.register(handle_menu_start, F.text == "Старт", StateFilter(QuizStates.intermediate))


def register_all_handlers(router: Router):
    register_start_handlers(router)
    register_intro_handlers(router)
    register_game_handlers(router)
    register_answer_handlers(router)
    register_hint_handlers(router)
    register_menu_handlers(router)

    # Обработчик для кнопки "Следующий вопрос"
    router.message.register(handle_next_question, StateFilter(QuizStates.intermediate), F.text == "Следующий вопрос")


register_all_handlers(router)
