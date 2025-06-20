from aiogram import types
from aiogram.dispatcher.filters import Command
from datetime import datetime
from sqlalchemy.orm import Session

# from app.main import dp
from app.utils.db import SessionLocal
from app.models.event import Event

# @dp.message_handler(Command('events'))
async def cmd_events(message: types.Message):
    session: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        events = (
            session.query(Event)
            .filter(Event.datetime >= now)
            .order_by(Event.datetime)
            .limit(5)
            .all()
        )
        if not events:
            await message.answer('Нет запланированных событий.')
            return
        lines = [
            f"📅 {e.datetime.strftime('%d.%m.%Y %H:%M')} — {e.title} (ментор: {e.mentor.name})"
            for e in events
        ]
        await message.answer('\n'.join(lines))
    finally:
        session.close()