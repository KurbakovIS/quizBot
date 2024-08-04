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

        await message.answer("нажимай Начать Викторину", reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(text="Начать Викторину")
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        ))

    await state.set_state(QuizStates.intro)


async def continue_intro(message: types.Message, state: FSMContext):
    await message.answer("Еще один текстовый блок перед началом игры.", reply_markup=types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text="Далее")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    ))
    await state.set_state(QuizStates.start)


async def start_game(message: types.Message, state: FSMContext):
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
            await repo.update_user_level(user, level.id)

        next_level = level
        while next_level:
            questions = await repo.get_questions_by_level(next_level.id)
            if questions:
                question = questions[0]
                await message.answer(question.text)
                await state.update_data(current_question_id=question.id, level_id=next_level.id)
                await state.set_state(QuizStates.question)
                return
            next_level = await repo.get_next_level(next_level.number)

        await message.answer("Нет доступных вопросов на данный момент.", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()


async def handle_answer(message: types.Message, state: FSMContext):
    async with UnitOfWork() as uow:
        repo = Repository(uow.session)
        data = await state.get_data()
        question_id = data.get('current_question_id')
        level_id = data.get('level_id')

        question = await repo.get_question_by_id(question_id)

        if question and message.text.lower() == question.correct_answer.lower():
            user = await repo.get_user_by_chat_id(str(message.chat.id))
            reward, correct_message, incorrect_message = await repo.get_level_reward_and_messages(level_id)
            await repo.update_user_balance(user, reward)
            await repo.mark_level_completed(user, level_id)
            await message.answer(f"{correct_message} Вы заработали {reward} points.")
            await state.clear()
        else:
            incorrect_message = question.incorrect_answer
            await message.answer(incorrect_message)
