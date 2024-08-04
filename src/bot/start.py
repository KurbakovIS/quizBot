from aiogram import types
from aiogram.fsm.context import FSMContext
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_message_with_optional_photo
from src.database.repository import Repository
from src.database.uow import UnitOfWork


async def start_bot(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        user = await repo.get_user_by_chat_id(str(message.chat.id))
        level = await repo.get_first_level()

        if not user:
            user = await repo.create_user(
                username=message.from_user.username,
                chat_id=str(message.chat.id),
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                current_level=level.id,
            )
        else:
            user_state = await repo.get_user_state(user.id)
            if user_state:
                await state.set_state(user_state.state)
                await state.update_data(**user_state.data)
                await message.answer("Восстановлено предыдущее состояние.")
                return
            await repo.update_user_level(user.id, level.id)
        await uow.flush()
        await repo.add_user_level_entry(user.id, level.id)

        text = level.intro_text
        await send_message_with_optional_photo(message, text, level.image_file)

        await message.answer("Нажимай Далее для продолжения", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text="Далее")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        ))

        await state.update_data(current_level_id=level.id, intro_levels_completed=0)
        await state.set_state(QuizStates.intro)
        await repo.update_user_state(user.id, QuizStates.intro.state, await state.get_data())
        await uow.commit()


async def continue_intro(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        current_level_id = data.get('current_level_id')
        intro_levels_completed = data.get('intro_levels_completed')
        user = await repo.get_user_by_chat_id(str(message.chat.id))

        next_level = await repo.get_next_level(current_level_id)
        if next_level and next_level.is_intro:
            await send_message_with_optional_photo(message, next_level.intro_text, next_level.image_file)
            await repo.add_user_level_entry(user.id, next_level.id)
            await repo.add_stage_completion(user.id, next_level.id)
            await repo.update_user_level(user.id, next_level.id)
            await state.update_data(current_level_id=next_level.id, intro_levels_completed=intro_levels_completed + 1)
            await state.set_state(QuizStates.intro)
        else:
            if next_level:
                await message.answer("Викторина начинается. Нажмите 'Далее' для первого вопроса.",
                                     reply_markup=types.ReplyKeyboardMarkup(
                                         keyboard=[
                                             [
                                                 types.KeyboardButton(text="Далее")
                                             ]
                                         ],
                                         resize_keyboard=True,
                                         one_time_keyboard=True
                                     ))
                await repo.add_user_level_entry(user.id, next_level.id)
                await repo.add_stage_completion(user.id, next_level.id)
                await repo.update_user_level(user.id, next_level.id)
                await state.update_data(current_level_id=next_level.id)
                await state.set_state(QuizStates.start)
            else:
                await message.answer("Все уровни Intro завершены, но уровни с вопросами не найдены.",
                                     reply_markup=types.ReplyKeyboardRemove())
                await state.clear()
        await repo.update_user_state(user.id, await state.get_state(), await state.get_data())
        await uow.commit()


async def start_game(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        current_level_id = data.get('current_level_id')
        user = await repo.get_user_by_chat_id(str(message.chat.id))

        questions = await repo.get_questions_by_level(current_level_id)
        if questions:
            question = questions[0]
            await send_message_with_optional_photo(message, question.text, question.image_file)
            await state.update_data(current_question_id=question.id)
            await repo.add_stage_completion(user.id, current_level_id)
            await state.set_state(QuizStates.question)
        else:
            next_level = await repo.get_next_level(current_level_id)
            if next_level:
                await state.update_data(current_level_id=next_level.id)
                await start_game(message, state)
            else:
                await message.answer("Нет доступных вопросов на данный момент.",
                                     reply_markup=types.ReplyKeyboardRemove())
                await state.clear()
        await repo.update_user_state(user.id, await state.get_state(), await state.get_data())
        await uow.commit()


async def handle_answer(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        question_id = data.get('current_question_id')
        current_level_id = data.get('current_level_id')
        user = await repo.get_user_by_chat_id(str(message.chat.id))

        question = await repo.get_question_by_id(question_id)

        if question and message.text.lower() == question.correct_answer.lower():
            reward = await repo.get_level_reward(current_level_id)
            await repo.update_user_balance(user.id, reward)
            await repo.mark_level_completed(user.id, current_level_id)
            await message.answer(f"Верно! Вы заработали {reward} points.")
        else:
            await message.answer("Неправильно. Попробуйте снова.")

        next_level = await repo.get_next_level(current_level_id)
        if next_level:
            await repo.add_user_level_entry(user.id, next_level.id)
            await state.update_data(current_level_id=next_level.id)
            await start_game(message, state)
        else:
            await message.answer("Все вопросы завершены.", reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
        await repo.update_user_state(user.id, await state.get_state(), await state.get_data())
        await uow.commit()
