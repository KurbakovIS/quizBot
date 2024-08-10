from src.database.repository import Repository
from src.database.uow import UnitOfWork
from aiogram.fsm.context import FSMContext

from src.dto.convert import question_to_dto


async def get_question_from_state(state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        question_id = data.get('current_question_id')
        find_question = await repo.get_question_by_id(question_id)
        question_dto = question_to_dto(find_question)
        return question_dto


def generate_hint_message(question):
    if question and question.hint:
        return f"Подсказка: {question.hint}"
    return "Подсказка недоступна для этого вопроса."
