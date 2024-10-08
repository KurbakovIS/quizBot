import os
from aiogram.types import FSInputFile
from loguru import logger


async def send_message_with_optional_photo(message, text, image_file=None):
    try:
        if image_file:
            file_path = os.path.abspath(image_file)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                photo = FSInputFile(path=file_path)
                try:
                    await message.answer_photo(photo, caption=text)
                except Exception as e:
                    logger.error(f"Failed to send photo: {e}")
                    await message.answer(text)
            else:
                logger.error(f"File not found or unsupported format: {file_path}")
                await message.answer(text)
        else:
            await message.answer(text)
    except Exception as e:
        logger.error(f"Error in send_message_with_optional_photo: {e}")
        await message.answer("Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.")
