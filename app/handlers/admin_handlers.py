from aiogram import Router
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.db.session import get_session
from app.models.mentor import Mentor
from app.models.event import Event
from app.models.record import Record
from app.utils.admin import AdminMiddleware
from app.utils.i18n import _

router = Router()
# Middleware проверки админа/ментора
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())

# FSM для добавления ментора
class MentorForm(StatesGroup):
    name = State()
    bio = State()
    contact = State()

@router.message(Command("add_mentor"))
async def cmd_add_mentor(message: Message, state: FSMContext):
    await state.set_state(MentorForm.name)
    await message.reply(_("Введите имя ментора:"))

@router.message(MentorForm.name)
async def mentor_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply(_("Введите био ментора:"))
    await state.set_state(MentorForm.bio)

@router.message(MentorForm.bio)
async def mentor_bio(message: Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await message.reply(_("Введите контакт (email или Telegram):"))
    await state.set_state(MentorForm.contact)

@router.message(MentorForm.contact)
async def mentor_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    new_mentor = Mentor(name=data['name'], bio=data['bio'], contact=message.text)
    async with state.proxy() as dp: pass
    session: AsyncSession = (await get_session().__anext__())
    session.add(new_mentor)
    await session.commit()
    await message.reply(_("Ментор добавлен."))
    await state.clear()

# Удаление ментора
@router.message(Command("remove_mentor"))
async def cmd_remove_mentor(message: Message, session: AsyncSession = Depends(get_session)):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.reply(_("Укажите ID или имя ментора для удаления."))
    key = parts[1]
    result = await session.execute(
        select(Mentor).where(
            (Mentor.id == key) | (Mentor.name == key)
        )
    )
    mentor = result.scalars().first()
    if mentor:
        await session.delete(mentor)
        await session.commit()
        await message.reply(_("Ментор удалён."))
    else:
        await message.reply(_("Ментор не найден."))

# FSM для добавления события
class EventForm(StatesGroup):
    title = State()
    description = State()
    datetime = State()
    category = State()
    mentor = State()

@router.message(Command("add_event"))
async def cmd_add_event(message: Message, state: FSMContext):
    await state.set_state(EventForm.title)
    await message.reply(_("Введите название события:"))

@router.message(EventForm.title)
async def event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.reply(_("Введите описание события:"))
    await state.set_state(EventForm.description)

@router.message(EventForm.description)
async def event_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.reply(_("Введите дату и время события (YYYY-MM-DD HH:MM):"))
    await state.set_state(EventForm.datetime)

@router.message(EventForm.datetime)
async def event_datetime(message: Message, state: FSMContext):
    await state.update_data(datetime=message.text)
    await message.reply(_("Введите категорию события:"))
    await state.set_state(EventForm.category)

@router.message(EventForm.category)
async def event_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    # Выбор ментора
    session: AsyncSession = (await get_session().__anext__())
    result = await session.execute(select(Mentor))
    mentors = result.scalars().all()
    kb = []
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    markup = InlineKeyboardMarkup()
    for m in mentors:
        markup.add(InlineKeyboardButton(text=m.name, callback_data=f"choose_mentor_{m.id}"))
    await message.reply(_("Выберите ментора:"), reply_markup=markup)
    await state.set_state(EventForm.mentor)

@router.callback_query(Text(startswith="choose_mentor_"), EventForm.mentor)
async def event_choose_mentor(callback: CallbackQuery, state: FSMContext):
    mentor_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    new_event = Event(
        title=data['title'],
        description=data['description'],
        datetime=data['datetime'],
        category=data['category'],
        mentor_id=mentor_id
    )
    session: AsyncSession = (await get_session().__anext__())
    session.add(new_event)
    await session.commit()
    await callback.message.edit_text(_("Событие добавлено."))
    await state.clear()

# FSM для загрузки записи
class RecordForm(StatesGroup):
    media = State()
    category = State()
    title = State()

@router.message(Command("upload_record"))
async def cmd_upload_record(message: Message, state: FSMContext):
    await state.set_state(RecordForm.media)
    await message.reply(_("Пришлите видеофайл или ссылку на запись:"))

@router.message(RecordForm.media)
async def record_media(message: Message, state: FSMContext):
    if message.video:
        file_url = message.video.file_id
    else:
        file_url = message.text
    await state.update_data(file_url=file_url)
    await message.reply(_("Введите категорию записи:"))
    await state.set_state(RecordForm.category)

@router.message(RecordForm.category)
async def record_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.reply(_("Введите название записи:"))
    await state.set_state(RecordForm.title)

@router.message(RecordForm.title)
async def record_title(message: Message, state: FSMContext):
    data = await state.get_data()
    new_rec = Record(title=message.text, category=data['category'], file_url=data['file_url'])
    session: AsyncSession = (await get_session().__anext__())
    session.add(new_rec)
    await session.commit()
    await message.reply(_("Запись загружена."))
    await state.clear()