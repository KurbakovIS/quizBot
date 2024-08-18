from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.filters.state import StateFilter

from src.bot.fsm.state_fsm import InfoCollectionStates
from src.bot.fsm.state_machine import (
    collect_name, collect_company, collect_position, confirm_info
)
from src.bot.gameplay.answer import handle_answer, handle_next_question, return_to_skipped_levels, \
    handle_skipped_level_choice
from src.bot.gameplay.game import start_game
from src.bot.gameplay.intro import continue_intro
from src.bot.handlers.handle_object_recognition import handle_object_recognition
from src.bot.handlers.menu.handlers import (
    handle_info, handle_comment, handle_demo,
    handle_shop, handle_subscribe, handle_menu_start, handle_purchase
)
from src.bot.start import start_bot
from src.bot.states import QuizStates
from src.bot.utils.levels import skip_level

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


def register_menu_command(router: Router, command: str, handler, state_filters):
    router.message.register(handler, Command(command), StateFilter(*state_filters))


def register_menu_handlers(router: Router):
    menu_commands = {
        "info": handle_info,
        "comment": handle_comment,
        "demo": handle_demo,
        "shop": handle_shop,
        "subscribe": handle_subscribe,
        "start": handle_menu_start,
    }
    state_filters = [QuizStates.intermediate, QuizStates.completed, QuizStates.return_to_skipped]
    for command, handler in menu_commands.items():
        register_menu_command(router, command, handler, state_filters)


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

    # Регистрация callback_query для покупки товара
    router.callback_query.register(handle_purchase)


register_all_handlers(router)
