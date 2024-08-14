from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.filters.state import StateFilter

from src.bot.handlers.answer import handle_answer, skip_level, return_to_skipped_levels, handle_skipped_level_choice, \
    handle_next_question
from src.bot.handlers.game import start_game
from src.bot.handlers.handle_object_recognition import handle_object_recognition
from src.bot.handlers.intro import continue_intro
from src.bot.handlers.menu.handlers import handle_info, handle_comment, handle_demo, handle_shop, handle_subscribe, \
    handle_menu_start
from src.bot.handlers.state_machine import collect_name, collect_company, collect_position, confirm_info
from src.bot.start import start_bot
from src.bot.state_machine import InfoCollectionStates
from src.bot.states import QuizStates

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


def register_info_collection_handlers(router: Router):
    router.message.register(collect_name, InfoCollectionStates.collecting_name)
    router.message.register(collect_company, InfoCollectionStates.collecting_company)
    router.message.register(collect_position, InfoCollectionStates.collecting_position)
    router.message.register(confirm_info, InfoCollectionStates.confirmation)


def register_object_recognition_handlers(router: Router):
    router.message.register(handle_object_recognition, StateFilter(QuizStates.object_recognition))


def register_handle_next_question(router: Router):
    router.message.register(handle_next_question, StateFilter(QuizStates.intermediate), F.text == "Следующий вопрос")


def register_all_handlers(router: Router):
    register_start_handlers(router)
    register_intro_handlers(router)
    register_game_handlers(router)
    register_answer_handlers(router)
    register_hint_handlers(router)
    register_menu_handlers(router)
    register_object_recognition_handlers(router)

    register_info_collection_handlers(router)

    register_handle_next_question(router)

    # Регистрация новых обработчиков
    router.message.register(skip_level, StateFilter(QuizStates.question), F.text == "Пропустить уровень")
    router.message.register(return_to_skipped_levels, StateFilter(QuizStates.completed),
                            F.text == "Вернуться на пропущенные уровни")
    router.message.register(handle_skipped_level_choice, StateFilter(QuizStates.return_to_skipped))


register_all_handlers(router)
