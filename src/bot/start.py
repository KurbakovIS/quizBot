from aiogram import types
from aiogram.fsm.context import FSMContext
from src.bot.states import QuizStates
from src.bot.utils.message_actions import send_level_message
from src.database.repository import Repository
from src.database.uow import UnitOfWork

async def start_bot(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        level = await repo.get_first_level()

        text = level.intro_text
        await send_level_message(message, level, text)

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
        await uow.commit()

async def continue_intro(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        current_level_id = data.get('current_level_id')
        intro_levels_completed = data.get('intro_levels_completed')

        next_level = await repo.get_next_level(current_level_id)
        if next_level and next_level.is_intro:
            await send_level_message(message, next_level, next_level.intro_text)
            await state.update_data(current_level_id=next_level.id, intro_levels_completed=intro_levels_completed + 1)
            await state.set_state(QuizStates.intro)
        else:
            if next_level:
                await send_level_message(message, next_level, next_level.intro_text)
                await state.update_data(current_level_id=next_level.id)
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
                await state.set_state(QuizStates.start)
            else:
                await message.answer("Все уровни Intro завершены, но уровни с вопросами не найдены.",
                                     reply_markup=types.ReplyKeyboardRemove())
                await state.clear()
        await uow.commit()

async def start_game(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        current_level_id = data.get('current_level_id')

        questions = await repo.get_questions_by_level(current_level_id)
        if questions:
            question = questions[0]
            await message.answer(question.text)
            await state.update_data(current_question_id=question.id)
            await state.set_state(QuizStates.question)
        else:
            next_level = await repo.get_next_level(current_level_id)
            if next_level:
                await state.update_data(current_level_id=next_level.id)
                await start_game(message, state)
            else:
                await message.answer("Нет доступных вопросов на данный момент.", reply_markup=types.ReplyKeyboardRemove())
                await state.clear()
        await uow.commit()

async def handle_answer(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        question_id = data.get('current_question_id')
        current_level_id = data.get('current_level_id')

        question = await repo.get_question_by_id(question_id)

        if question and message.text.lower() == question.correct_answer.lower():
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            reward = await repo.get_level_reward_and_messages(current_level_id)
            await repo.update_user_balance(user, reward)
            await repo.mark_level_completed(user, current_level_id)
            await message.answer(f"Верно! Вы заработали {reward} points.")
        else:
            await message.answer("Неправильно. Попробуйте снова.")

        next_level = await repo.get_next_level(current_level_id)
        if next_level:
            await state.update_data(current_level_id=next_level.id)
            await start_game(message, state)
        else:
            await message.answer("Все вопросы завершены.", reply_markup=types.ReplyKeyboardRemove())
            await state.clear()
        await uow.commit()
