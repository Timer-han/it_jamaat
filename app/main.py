import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import SimpleI18nMiddleware

# корректные относительно app/ директории импорты
from config import config
from utils.i18n import I18N, _
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    # i18n middleware
    dp.message.middleware(SimpleI18nMiddleware(I18N, default_locale="ru"))

    # include routers
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # /start command handler
    @dp.message(Command("start"))
    async def start_handler(message: Message):
        await message.answer(_("Добро пожаловать в IT Jama'at Bot!"))

    logger.info("Bot started")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())