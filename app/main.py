import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.user_handlers import router
from handlers.admin_handlers import admin_router
from database.database import init_db
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключение роутеров
    dp.include_router(router)
    dp.include_router(admin_router)
    
    # Инициализация базы данных
    await init_db()
    
    # Запуск поллинга
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())