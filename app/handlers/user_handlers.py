from datetime import datetime
from aiogram import Router
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_session
from app.models.mentor import Mentor
from app.models.event import Event
from app.models.record import Record
from app.models.vacancy import Vacancy
from app.models.project import Project
from app.utils.i18n import _

router = Router()

@router.message(Command("events"))
async def events_handler(message: Message, session: AsyncSession = Depends(get_session)):
    now = datetime.utcnow()
    result = await session.execute(
        select(Event).where(Event.datetime >= now).order_by(Event.datetime).limit(5)
    )
    events = result.scalars().all()
    if not events:
        return await message.reply(_("Событий нет."))
    lines = [f"📅 {e.datetime.strftime('%Y-%m-%d %H:%M')} — {e.title} (ментор: {e.mentor.name})" for e in events]
    await message.reply(_("Ближайшие события:") + "\n" + "\n".join(lines))

@router.message(Command("mentors"))
async def mentors_handler(message: Message, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Mentor))
    mentors = result.scalars().all()
    if not mentors:
        return await message.reply(_("Менторов нет."))
    lines = []
    for m in mentors:
        ev = await session.execute(
            select(Event)
            .where(Event.mentor_id == m.id, Event.datetime >= datetime.utcnow())
            .order_by(Event.datetime)
            .limit(1)
        )
        first = ev.scalars().first()
        if first:
            lines.append(f"👤 {m.name} — след. событие: {first.title} ({first.datetime.strftime('%Y-%m-%d %H:%M')})")
        else:
            lines.append(f"👤 {m.name} — нет запланированных событий")
    await message.reply(_("Менторы и их ближайшие события:") + "\n" + "\n".join(lines))

@router.message(Command("records"))
async def records_menu(message: Message, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Record.category).distinct())
    categories = [row[0] for row in result.all()]
    if not categories:
        return await message.reply(_("Записей нет."))
    kb = InlineKeyboardMarkup(row_width=2)
    for cat in categories:
        kb.add(InlineKeyboardButton(text=cat, callback_data=f"rec_{cat}"))
    await message.answer(_("Выберите категорию записей:"), reply_markup=kb)

@router.callback_query(Text(startswith="rec_"))
async def records_show(callback: CallbackQuery, session: AsyncSession = Depends(get_session)):
    category = callback.data.split("_")[1]
    result = await session.execute(select(Record).where(Record.category == category))
    recs = result.scalars().all()
    if not recs:
        return await callback.message.edit_text(_("Записей в этой категории нет."))
    lines = [f"▶️ {r.title}: {r.file_url}" for r in recs]
    await callback.message.edit_text(_("Записи по категории {category}:").format(category=category) + "\n" + "\n".join(lines))

@router.message(Command("vacancies"))
async def vacancies_handler(message: Message, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Vacancy).order_by(Vacancy.id.desc()).limit(5))
    vacs = result.scalars().all()
    if not vacs:
        return await message.reply(_("Вакансий нет."))
    lines = [f"💼 {v.title}: {v.link}" for v in vacs]
    await message.reply(_("Последние вакансии:") + "\n" + "\n".join(lines))

@router.message(Command("projects"))
async def projects_handler(message: Message, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Project).where(Project.is_active))
    projects = result.scalars().all()
    if not projects:
        return await message.reply(_("Активных проектов нет."))
    for p in projects:
        text = f"🚀 {p.title}\nТребуются: {p.required_roles}\nОписание: {p.description}"
        await message.reply(text)