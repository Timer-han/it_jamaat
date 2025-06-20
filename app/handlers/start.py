from aiogram import types
# from app.main import dp

# @dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user = message.from_user.first_name or 'there'
    await message.answer(f'Привет, {user}! Добро пожаловать!')