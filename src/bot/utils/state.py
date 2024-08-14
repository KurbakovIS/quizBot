from aiogram.fsm.context import FSMContext
from src.database.repository import Repository


async def update_user_state(repo: Repository, user_id: int, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await repo.update_user_state(user_id, current_state, await state.get_data())
