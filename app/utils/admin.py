from aiogram.dispatcher.middlewares.base import BaseMiddleware
from app.config import config

class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id
        if user_id not in config.ADMINS:
            return
        return await handler(event, data)