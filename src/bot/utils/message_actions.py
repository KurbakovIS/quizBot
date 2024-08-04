import os

from aiogram.types import FSInputFile
from loguru import logger


async def send_level_message(message, level, text):
    if level and level.image_file:
        file_path = os.path.abspath(level.image_file)  # Convert the path to an absolute path
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
