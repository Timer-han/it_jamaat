import logging
from aiogram import Bot, Dispatcher, executor
from app.config import config
from app.handlers import register_handlers

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

# Регистрируем все хендлеры
register_handlers(dp)

if __name__ == '__main__':
    logger.info('Бот запущен')
    executor.start_polling(dp, skip_updates=True)