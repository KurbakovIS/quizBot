from uuid import UUID

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.database.repository import Repository


async def update_user_state(repo: Repository, state: FSMContext, user_id: UUID):
    current_state = await state.get_state()
    if current_state:
        await repo.update_user_state(user_id, current_state, await state.get_data())


async def set_next_level_state(message: Message, state: FSMContext, next_state, repo: Repository):
    await state.set_state(next_state)
    user = await repo.get_user_by_chat_id(str(message.chat.id))
    await update_user_state(repo, state, user.id)
