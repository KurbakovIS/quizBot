async def skip_command(message):
    if message.text.startswith('/'):
        # Игнорируем команды, отправляем уведомление, если нужно
        await message.answer("Пожалуйста, завершите ввод данных перед использованием команды.")
        return