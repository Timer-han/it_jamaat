from aiogram import Dispatcher

from .start import cmd_start
from .help import cmd_help
from .events import cmd_events


def register_handlers(dp: Dispatcher):
    """Регистрация всех хендлеров бота"""
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(cmd_help, commands=['help'])
    dp.register_message_handler(cmd_events, commands=['events'])