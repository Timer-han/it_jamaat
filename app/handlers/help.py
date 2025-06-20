from aiogram import types
# from app.main import dp

# @dp.message_handler(commands=['help'])
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "Доступные команды:\n"
        "/start — начать работу с ботом\n"
        "/help — список доступных команд\n"
        "/events — ближайшие события"
    )
    await message.answer(help_text)
