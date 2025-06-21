# IT Jama'at Telegram Bot MVP
# Структура проекта и основные файлы

# 1. requirements.txt
"""
aiogram==3.4.1
asyncpg==0.29.0
python-dotenv==1.0.0
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
aiofiles==23.2.1
pillow==10.2.0
"""

# 2. .env (создать и заполнить своими данными)
"""
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/it_jamaate
ADMIN_IDS=123456789,987654321
"""

# 3. docker-compose.yml
"""
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: it_jamaate
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  bot:
    build: .
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/it_jamaate
    volumes:
      - ./media:/app/media
      - .env:/app/.env

volumes:
  postgres_data:
"""

# 4. Dockerfile
"""
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-u", "app/main.py"]
"""

# 5. app/database/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Связующая таблица для проектов и специальностей
project_skills = Table('project_skills', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('skill', String(50))
)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(50))
    full_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_mentor = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Mentor(Base):
    __tablename__ = 'mentors'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(100), nullable=False)
    bio = Column(Text)
    specialization = Column(String(100))
    contact_info = Column(String(200))
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", backref="mentor_profile")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))  # lecture, meeting, seminar
    mentor_id = Column(Integer, ForeignKey('mentors.id'))
    date_time = Column(DateTime, nullable=False)
    location = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    mentor = relationship("Mentor", backref="events")
    creator = relationship("User", backref="created_events")

class Lecture(Base):
    __tablename__ = 'lectures'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    mentor_id = Column(Integer, ForeignKey('mentors.id'))
    file_path = Column(String(500))
    video_url = Column(String(500))
    duration = Column(Integer)  # в минутах
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    
    mentor = relationship("Mentor", backref="lectures")
    uploader = relationship("User", backref="uploaded_lectures")

class Vacancy(Base):
    __tablename__ = 'vacancies'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    company = Column(String(100))
    description = Column(Text)
    requirements = Column(Text)
    salary_range = Column(String(100))
    location = Column(String(100))
    contact_info = Column(String(200))
    is_active = Column(Boolean, default=True)
    posted_at = Column(DateTime, default=datetime.utcnow)
    posted_by = Column(Integer, ForeignKey('users.id'))
    
    poster = relationship("User", backref="posted_vacancies")

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='discussion')  # discussion, development, completed
    required_skills = Column(Text)  # JSON строка со списком навыков
    contact_person = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    contact = relationship("User", backref="managed_projects")


# 6. app/database/database.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from .models import Base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 7. app/handlers/user_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from database.database import AsyncSessionLocal
from database.models import Event, Mentor, Lecture, Vacancy, Project, User
from datetime import datetime, timedelta
import json

router = Router()

@router.message(Command("start"))
async def start_command(message: Message):
    async with AsyncSessionLocal() as session:
        # Регистрируем пользователя если его нет
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )
            session.add(user)
            await session.commit()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Мероприятия", callback_data="events")],
        [InlineKeyboardButton(text="👨‍🏫 Менторы", callback_data="mentors")],
        [InlineKeyboardButton(text="📚 Лекции", callback_data="lectures")],
        [InlineKeyboardButton(text="💼 Вакансии", callback_data="vacancies")],
        [InlineKeyboardButton(text="🚀 Проекты", callback_data="projects")]
    ])
    
    await message.answer(
        "Ассаляму алейкум! Добро пожаловать в IT Jama'at! 🕌💻\n\n"
        "Здесь мусульмане-айтишники находят единомышленников, учатся и развиваются вместе.\n\n"
        "Выберите интересующий раздел:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == "events")
async def show_events(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        # Получаем ближайшие мероприятия
        result = await session.execute(
            select(Event)
            .options(selectinload(Event.mentor))
            .where(and_(Event.is_active == True, Event.date_time > datetime.utcnow()))
            .order_by(Event.date_time)
            .limit(10)
        )
        events = result.scalars().all()
    
    if not events:
        await callback.message.edit_text("📅 Пока нет запланированных мероприятий")
        return
    
    text = "📅 **Ближайшие мероприятия:**\n\n"
    for event in events:
        mentor_name = event.mentor.name if event.mentor else "Не указан"
        text += f"🔸 **{event.title}**\n"
        text += f"📍 {event.location or 'Онлайн'}\n"
        text += f"⏰ {event.date_time.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"👨‍🏫 {mentor_name}\n"
        if event.description:
            text += f"📝 {event.description[:100]}...\n"
        text += "\n"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "mentors")
async def show_mentors(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Mentor).where(Mentor.is_active == True)
        )
        mentors = result.scalars().all()
    
    if not mentors:
        await callback.message.edit_text("👨‍🏫 Пока нет активных менторов")
        return
    
    text = "👨‍🏫 **Наши менторы:**\n\n"
    for mentor in mentors:
        text += f"🔸 **{mentor.name}**\n"
        text += f"💼 {mentor.specialization or 'Специализация не указана'}\n"
        if mentor.bio:
            text += f"📝 {mentor.bio[:100]}...\n"
        if mentor.contact_info:
            text += f"📞 {mentor.contact_info}\n"
        text += "\n"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "lectures")
async def show_lectures(callback: CallbackQuery):
    # Показываем категории лекций
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Программирование", callback_data="lectures_programming")],
        [InlineKeyboardButton(text="🔒 Кибербезопасность", callback_data="lectures_security")],
        [InlineKeyboardButton(text="📊 Data Science", callback_data="lectures_data")],
        [InlineKeyboardButton(text="🌐 Web разработка", callback_data="lectures_web")],
        [InlineKeyboardButton(text="📱 Mobile разработка", callback_data="lectures_mobile")],
        [InlineKeyboardButton(text="🎯 Все лекции", callback_data="lectures_all")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "📚 **Выберите категорию лекций:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("lectures_"))
async def show_lectures_by_category(callback: CallbackQuery):
    category = callback.data.replace("lectures_", "")
    
    async with AsyncSessionLocal() as session:
        if category == "all":
            result = await session.execute(
                select(Lecture).options(selectinload(Lecture.mentor)).order_by(Lecture.uploaded_at.desc())
            )
        else:
            category_map = {
                "programming": "Программирование",
                "security": "Кибербезопасность", 
                "data": "Data Science",
                "web": "Web разработка",
                "mobile": "Mobile разработка"
            }
            result = await session.execute(
                select(Lecture)
                .options(selectinload(Lecture.mentor))
                .where(Lecture.category == category_map.get(category, category))
                .order_by(Lecture.uploaded_at.desc())
            )
        
        lectures = result.scalars().all()
    
    if not lectures:
        await callback.message.edit_text("📚 В данной категории пока нет лекций")
        return
    
    text = f"📚 **Лекции {'по всем категориям' if category == 'all' else category_map.get(category, category)}:**\n\n"
    
    for lecture in lectures[:10]:  # Показываем первые 10
        mentor_name = lecture.mentor.name if lecture.mentor else "Неизвестно"
        text += f"🔸 **{lecture.title}**\n"
        text += f"👨‍🏫 {mentor_name}\n"
        text += f"📂 {lecture.category or 'Без категории'}\n"
        if lecture.duration:
            text += f"⏱ {lecture.duration} мин\n"
        if lecture.description:
            text += f"📝 {lecture.description[:80]}...\n"
        text += f"📅 {lecture.uploaded_at.strftime('%d.%m.%Y')}\n\n"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К категориям", callback_data="lectures")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "vacancies")
async def show_vacancies(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Vacancy).where(Vacancy.is_active == True).order_by(Vacancy.posted_at.desc())
        )
        vacancies = result.scalars().all()
    
    if not vacancies:
        await callback.message.edit_text("💼 Пока нет активных вакансий")
        return
    
    text = "💼 **Актуальные вакансии:**\n\n"
    for vacancy in vacancies[:10]:
        text += f"🔸 **{vacancy.title}**\n"
        text += f"🏢 {vacancy.company or 'Компания не указана'}\n"
        if vacancy.salary_range:
            text += f"💰 {vacancy.salary_range}\n"
        text += f"📍 {vacancy.location or 'Не указано'}\n"
        if vacancy.description:
            text += f"📝 {vacancy.description[:100]}...\n"
        if vacancy.contact_info:
            text += f"📞 {vacancy.contact_info}\n"
        text += "\n"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "projects")
async def show_projects(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Project)
            .options(selectinload(Project.contact))
            .where(Project.is_active == True)
            .order_by(Project.created_at.desc())
        )
        projects = result.scalars().all()
    
    if not projects:
        await callback.message.edit_text("🚀 Пока нет активных проектов")
        return
    
    text = "🚀 **Активные проекты:**\n\n"
    for project in projects[:10]:
        status_emoji = {"discussion": "💬", "development": "⚙️", "completed": "✅"}
        status_text = {"discussion": "Обсуждение", "development": "Разработка", "completed": "Завершен"}
        
        text += f"🔸 **{project.title}**\n"
        text += f"{status_emoji.get(project.status, '📋')} {status_text.get(project.status, project.status)}\n"
        if project.description:
            text += f"📝 {project.description[:100]}...\n"
        if project.required_skills:
            text += f"🛠 Нужны: {project.required_skills[:50]}...\n"
        text += f"📅 {project.created_at.strftime('%d.%m.%Y')}\n\n"
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Мероприятия", callback_data="events")],
        [InlineKeyboardButton(text="👨‍🏫 Менторы", callback_data="mentors")],
        [InlineKeyboardButton(text="📚 Лекции", callback_data="lectures")],
        [InlineKeyboardButton(text="💼 Вакансии", callback_data="vacancies")],
        [InlineKeyboardButton(text="🚀 Проекты", callback_data="projects")]
    ])
    
    await callback.message.edit_text(
        "🕌💻 **IT Jama'at**\n\n"
        "Выберите интересующий раздел:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# 8. handlers/admin_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.database import AsyncSessionLocal
from database.models import User, Mentor, Event, Lecture
import os
from datetime import datetime, timedelta

admin_router = Router()

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

class AdminStates(StatesGroup):
    adding_mentor = State()
    mentor_name = State()
    mentor_bio = State()
    mentor_specialization = State()
    mentor_contact = State()
    
    adding_event = State()
    event_title = State()
    event_description = State()
    event_datetime = State()
    event_location = State()
    
    # States for editing events
    editing_event = State()
    edit_event_title = State()
    edit_event_description = State()
    edit_event_datetime = State()
    edit_event_location = State()
    edit_event_mentors = State()

async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ментора", callback_data="admin_add_mentor")],
        [InlineKeyboardButton(text="➖ Удалить ментора", callback_data="admin_remove_mentor")],
        [InlineKeyboardButton(text="📅 Добавить мероприятие", callback_data="admin_add_event")],
        [InlineKeyboardButton(text="✏️ Редактировать мероприятие", callback_data="admin_edit_event")],
        [InlineKeyboardButton(text="🗑 Удалить мероприятие", callback_data="admin_delete_event")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])
    
    await message.answer("🔧 **Панель администратора**", reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "admin_add_mentor")
async def start_add_mentor(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    
    await callback.message.edit_text("👨‍🏫 Введите имя нового ментора:")
    await state.set_state(AdminStates.mentor_name)

@admin_router.message(AdminStates.mentor_name)
async def get_mentor_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Введите специализацию ментора:")
    await state.set_state(AdminStates.mentor_specialization)

@admin_router.message(AdminStates.mentor_specialization)
async def get_mentor_specialization(message: Message, state: FSMContext):
    await state.update_data(specialization=message.text)
    await message.answer("📖 Введите краткое описание ментора:")
    await state.set_state(AdminStates.mentor_bio)

@admin_router.message(AdminStates.mentor_bio)
async def get_mentor_bio(message: Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await message.answer("📞 Введите контактную информацию ментора:")
    await state.set_state(AdminStates.mentor_contact)

@admin_router.message(AdminStates.mentor_contact)
async def save_mentor(message: Message, state: FSMContext):
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        mentor = Mentor(
            name=data['name'],
            specialization=data['specialization'],
            bio=data['bio'],
            contact_info=message.text
        )
        session.add(mentor)
        await session.commit()
    
    await message.answer(f"✅ Ментор **{data['name']}** успешно добавлен!", parse_mode="Markdown")
    await state.clear()

@admin_router.callback_query(F.data == "admin_add_event")
async def start_add_event(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        return
    
    # Добавляем кнопку отмены
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_event")]
    ])
    
    await callback.message.edit_text("📅 Введите название мероприятия:", reply_markup=keyboard)
    await state.set_state(AdminStates.event_title)

@admin_router.message(AdminStates.event_title)
async def get_event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    
    # Добавляем кнопку отмены
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_event")]
    ])
    
    await message.answer("📝 Введите описание мероприятия:", reply_markup=keyboard)
    await state.set_state(AdminStates.event_description)

@admin_router.message(AdminStates.event_description)
async def get_event_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    # Добавляем кнопку отмены
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_event")]
    ])
    
    await message.answer("⏰ Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ:", reply_markup=keyboard)
    await state.set_state(AdminStates.event_datetime)

@admin_router.message(AdminStates.event_datetime)
async def get_event_datetime(message: Message, state: FSMContext):
    try:
        event_datetime = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(datetime=event_datetime)
        
        # Добавляем кнопку отмены
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_event")]
        ])
        
        await message.answer("📍 Введите место проведения:", reply_markup=keyboard)
        await state.set_state(AdminStates.event_location)
    except ValueError:
        # Показываем кнопку отмены даже при ошибке
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_event")]
        ])
        await message.answer("❌ Неверный формат! Используйте ДД.ММ.ГГГГ ЧЧ:ММ", reply_markup=keyboard)

# Новый обработчик для отмены создания мероприятия
@admin_router.callback_query(F.data == "cancel_add_event")
async def cancel_add_event(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    # Возвращаемся в панель администратора
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ментора", callback_data="admin_add_mentor")],
        [InlineKeyboardButton(text="➖ Удалить ментора", callback_data="admin_remove_mentor")],
        [InlineKeyboardButton(text="📅 Добавить мероприятие", callback_data="admin_add_event")],
        [InlineKeyboardButton(text="✏️ Редактировать мероприятие", callback_data="admin_edit_event")],
        [InlineKeyboardButton(text="🗑 Удалить мероприятие", callback_data="admin_delete_event")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(
        "❌ Создание мероприятия отменено.\n\n🔧 **Панель администратора**", 
        reply_markup=keyboard, 
        parse_mode="Markdown"
    )

# Редактирование мероприятий
@admin_router.callback_query(F.data == "admin_edit_event")
async def select_event_to_edit(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Event)
            .options(selectinload(Event.mentor))
            .where(Event.is_active == True)
            .order_by(Event.date_time)
        )
        events = result.scalars().all()
    
    if not events:
        await callback.message.edit_text("📅 Нет активных мероприятий для редактирования")
        return
    
    keyboard_buttons = []
    for event in events[:10]:  # Показываем первые 10
        event_text = f"{event.title} ({event.date_time.strftime('%d.%m %H:%M')})"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=event_text[:50] + "...",
                callback_data=f"show_edit_options_{event.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(
        "✏️ **Выберите мероприятие для редактирования:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@admin_router.callback_query(F.data.startswith("show_edit_options_"))
async def show_edit_options(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Event).options(selectinload(Event.mentor)).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
    
    if not event:
        await callback.message.edit_text("❌ Мероприятие не найдено")
        return
    
    mentor_name = event.mentor.name if event.mentor else "Не назначен"
    text = f"📅 **Мероприятие:** {event.title}\n"
    text += f"📝 **Описание:** {event.description or 'Не указано'}\n"
    text += f"⏰ **Дата:** {event.date_time.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"📍 **Место:** {event.location or 'Не указано'}\n"
    text += f"👨‍🏫 **Ментор:** {mentor_name}\n\n"
    text += "Что хотите изменить?"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data=f"edit_title_{event_id}")],
        [InlineKeyboardButton(text="📄 Описание", callback_data=f"edit_desc_{event_id}")],
        [InlineKeyboardButton(text="⏰ Дата и время", callback_data=f"edit_datetime_{event_id}")],
        [InlineKeyboardButton(text="📍 Место", callback_data=f"edit_location_{event_id}")],
        [InlineKeyboardButton(text="👨‍🏫 Назначить ментора", callback_data=f"edit_mentor_{event_id}")],
        [InlineKeyboardButton(text="◀️ К списку мероприятий", callback_data="admin_edit_event")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data.startswith("edit_title_"))
async def edit_event_title(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_event_id=event_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"show_edit_options_{event_id}")]
    ])
    
    await callback.message.edit_text("📝 Введите новое название мероприятия:", reply_markup=keyboard)
    await state.set_state(AdminStates.edit_event_title)

@admin_router.message(AdminStates.edit_event_title)
async def save_edited_title(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data['editing_event_id']
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one()
        event.title = message.text
        await session.commit()
    
    await message.answer(f"✅ Название изменено на: **{message.text}**", parse_mode="Markdown")
    await state.clear()

@admin_router.callback_query(F.data.startswith("edit_desc_"))
async def edit_event_description(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_event_id=event_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"show_edit_options_{event_id}")]
    ])
    
    await callback.message.edit_text("📄 Введите новое описание мероприятия:", reply_markup=keyboard)
    await state.set_state(AdminStates.edit_event_description)

@admin_router.message(AdminStates.edit_event_description)
async def save_edited_description(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data['editing_event_id']
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one()
        event.description = message.text
        await session.commit()
    
    await message.answer("✅ Описание успешно изменено!")
    await state.clear()

@admin_router.callback_query(F.data.startswith("edit_datetime_"))
async def edit_event_datetime(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_event_id=event_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"show_edit_options_{event_id}")]
    ])
    
    await callback.message.edit_text("⏰ Введите новую дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ:", reply_markup=keyboard)
    await state.set_state(AdminStates.edit_event_datetime)

@admin_router.message(AdminStates.edit_event_datetime)
async def save_edited_datetime(message: Message, state: FSMContext):
    try:
        new_datetime = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        data = await state.get_data()
        event_id = data['editing_event_id']
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Event).where(Event.id == event_id))
            event = result.scalar_one()
            event.date_time = new_datetime
            await session.commit()
        
        await message.answer(f"✅ Дата изменена на: **{new_datetime.strftime('%d.%m.%Y %H:%M')}**", parse_mode="Markdown")
        await state.clear()
    except ValueError:
        await message.answer("❌ Неверный формат! Используйте ДД.ММ.ГГГГ ЧЧ:ММ")

@admin_router.callback_query(F.data.startswith("edit_location_"))
async def edit_event_location(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_event_id=event_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"show_edit_options_{event_id}")]
    ])
    
    await callback.message.edit_text("📍 Введите новое место проведения:", reply_markup=keyboard)
    await state.set_state(AdminStates.edit_event_location)

@admin_router.message(AdminStates.edit_event_location)
async def save_edited_location(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data['editing_event_id']
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one()
        event.location = message.text
        await session.commit()
    
    await message.answer(f"✅ Место изменено на: **{message.text}**", parse_mode="Markdown")
    await state.clear()

@admin_router.callback_query(F.data.startswith("edit_mentor_"))
async def edit_event_mentor(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_event_id=event_id)
    
    # Получаем текущего ментора мероприятия и всех доступных менторов
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Event).options(selectinload(Event.mentor)).where(Event.id == event_id)
        )
        event = result.scalar_one()
        current_mentor_id = event.mentor.id if event.mentor else None
        
        # Получаем всех активных менторов
        result = await session.execute(
            select(Mentor).where(Mentor.is_active == True)
        )
        all_mentors = result.scalars().all()
    
    if not all_mentors:
        await callback.message.edit_text("❌ Нет доступных менторов")
        return
    
    # Создаем клавиатуру с менторами
    keyboard_buttons = []
    
    # Кнопка "Без ментора"
    no_mentor_emoji = "✅" if current_mentor_id is None else "❌"
    keyboard_buttons.append([
        InlineKeyboardButton(
            text=f"{no_mentor_emoji} Без ментора",
            callback_data=f"assign_mentor_none_{event_id}"
        )
    ])
    
    for mentor in all_mentors:
        # Показываем галочку если это текущий ментор
        emoji = "✅" if mentor.id == current_mentor_id else "👨‍🏫"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {mentor.name}",
                callback_data=f"assign_mentor_{mentor.id}_{event_id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"show_edit_options_{event_id}")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    current_mentor_text = event.mentor.name if event.mentor else "Не назначен"
    await callback.message.edit_text(
        f"👨‍🏫 **Назначение ментора мероприятию**\n\n"
        f"Текущий ментор: **{current_mentor_text}**\n\n"
        "Выберите нового ментора:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@admin_router.callback_query(F.data.startswith("assign_mentor_"))
async def assign_mentor_to_event(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    if parts[2] == "none":
        mentor_id = None
        event_id = int(parts[3])
    else:
        mentor_id = int(parts[2])
        event_id = int(parts[3])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one()
        
        # Назначаем ментора
        event.mentor_id = mentor_id
        await session.commit()
        
        # Получаем имя ментора для отображения
        mentor_name = "не назначен"
        if mentor_id:
            result = await session.execute(
                select(Mentor).where(Mentor.id == mentor_id)
            )
            mentor = result.scalar_one()
            mentor_name = mentor.name
    
    await callback.message.edit_text(
        f"✅ Ментор мероприятия успешно обновлен!\n\n"
        f"Назначенный ментор: **{mentor_name}**",
        parse_mode="Markdown"
    )
    await state.clear()

# Удаление мероприятий
@admin_router.callback_query(F.data == "admin_delete_event")
async def select_event_to_delete(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Event)
            .options(selectinload(Event.mentor))
            .where(Event.is_active == True)
            .order_by(Event.date_time)
        )
        events = result.scalars().all()
    
    if not events:
        await callback.message.edit_text("📅 Нет активных мероприятий для удаления")
        return
    
    keyboard_buttons = []
    for event in events[:10]:
        event_text = f"{event.title} ({event.date_time.strftime('%d.%m %H:%M')})"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=event_text[:50] + "...",
                callback_data=f"delete_event_{event.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(
        "🗑 **Выберите мероприятие для удаления:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@admin_router.callback_query(F.data.startswith("delete_event_"))
async def confirm_delete_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
    
    if not event:
        await callback.message.edit_text("❌ Мероприятие не найдено")
        return
    
    text = f"🗑 **Подтвердите удаление мероприятия:**\n\n"
    text += f"📅 **Название:** {event.title}\n"
    text += f"⏰ **Дата:** {event.date_time.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"📍 **Место:** {event.location or 'Не указано'}\n\n"
    text += "⚠️ **Это действие нельзя отменить!**"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_delete_{event_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_delete_event")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data.startswith("confirm_delete_"))
async def delete_event_confirmed(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        
        if event:
            # Помечаем как неактивное вместо физического удаления
            event.is_active = False
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ Мероприятие **{event.title}** успешно удалено!",
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text("❌ Мероприятие не найдено")

# Удаление менторов
@admin_router.callback_query(F.data == "admin_remove_mentor")
async def select_mentor_to_remove(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Mentor).where(Mentor.is_active == True)
        )
        mentors = result.scalars().all()
    
    if not mentors:
        await callback.message.edit_text("👨‍🏫 Нет активных менторов для удаления")
        return
    
    keyboard_buttons = []
    for mentor in mentors:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{mentor.name} ({mentor.specialization})",
                callback_data=f"remove_mentor_{mentor.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(
        "👨‍🏫 **Выберите ментора для удаления:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@admin_router.callback_query(F.data.startswith("remove_mentor_"))
async def confirm_remove_mentor(callback: CallbackQuery):
    mentor_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Mentor).where(Mentor.id == mentor_id)
        )
        mentor = result.scalar_one_or_none()
    
    if not mentor:
        await callback.message.edit_text("❌ Ментор не найден")
        return
    
    text = f"🗑 **Подтвердите удаление ментора:**\n\n"
    text += f"👨‍🏫 **Имя:** {mentor.name}\n"
    text += f"💼 **Специализация:** {mentor.specialization}\n\n"
    text += "⚠️ **Это действие нельзя отменить!**"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_remove_mentor_{mentor_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_remove_mentor")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data.startswith("confirm_remove_mentor_"))
async def remove_mentor_confirmed(callback: CallbackQuery):
    mentor_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Mentor).where(Mentor.id == mentor_id))
        mentor = result.scalar_one_or_none()
        
        if mentor:
            # Помечаем как неактивного
            mentor.is_active = False
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ Ментор **{mentor.name}** успешно удален!",
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text("❌ Ментор не найден")

@admin_router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        # Общая статистика пользователей
        users_result = await session.execute(select(User))
        total_users = len(users_result.scalars().all())
        
        # Количество активных менторов
        mentors_result = await session.execute(
            select(Mentor).where(Mentor.is_active == True)
        )
        active_mentors = len(mentors_result.scalars().all())
        
        # Количество активных мероприятий
        events_result = await session.execute(
            select(Event).where(Event.is_active == True)
        )
        active_events = len(events_result.scalars().all())
        
        # Количество будущих мероприятий
        future_events_result = await session.execute(
            select(Event).where(
                and_(Event.is_active == True, Event.date_time > datetime.utcnow())
            )
        )
        future_events = len(future_events_result.scalars().all())
        
        # Количество прошедших мероприятий
        past_events_result = await session.execute(
            select(Event).where(
                and_(Event.is_active == True, Event.date_time <= datetime.utcnow())
            )
        )
        past_events = len(past_events_result.scalars().all())
        
        # Количество лекций
        lectures_result = await session.execute(select(Lecture))
        total_lectures = len(lectures_result.scalars().all())
        
        # Количество активных вакансий
        vacancies_result = await session.execute(
            select(Vacancy).where(Vacancy.is_active == True)
        )
        active_vacancies = len(vacancies_result.scalars().all())
        
        # Количество активных проектов
        projects_result = await session.execute(
            select(Project).where(Project.is_active == True)
        )
        active_projects = len(projects_result.scalars().all())
        
        # Статистика по статусам проектов
        discussion_projects = await session.execute(
            select(Project).where(
                and_(Project.is_active == True, Project.status == 'discussion')
            )
        )
        discussion_count = len(discussion_projects.scalars().all())
        
        development_projects = await session.execute(
            select(Project).where(
                and_(Project.is_active == True, Project.status == 'development')
            )
        )
        development_count = len(development_projects.scalars().all())
        
        completed_projects = await session.execute(
            select(Project).where(
                and_(Project.is_active == True, Project.status == 'completed')
            )
        )
        completed_count = len(completed_projects.scalars().all())
        
        # Статистика по категориям лекций
        programming_lectures = await session.execute(
            select(Lecture).where(Lecture.category == 'Программирование')
        )
        programming_count = len(programming_lectures.scalars().all())
        
        security_lectures = await session.execute(
            select(Lecture).where(Lecture.category == 'Кибербезопасность')
        )
        security_count = len(security_lectures.scalars().all())
        
        data_lectures = await session.execute(
            select(Lecture).where(Lecture.category == 'Data Science')
        )
        data_count = len(data_lectures.scalars().all())
        
        web_lectures = await session.execute(
            select(Lecture).where(Lecture.category == 'Web разработка')
        )
        web_count = len(web_lectures.scalars().all())
        
        mobile_lectures = await session.execute(
            select(Lecture).where(Lecture.category == 'Mobile разработка')
        )
        mobile_count = len(mobile_lectures.scalars().all())
    
    # Формируем текст статистики
    text = "📊 **Статистика IT Jama'at**\n\n"
    
    text += "👥 **Пользователи:**\n"
    text += f"• Всего пользователей: {total_users}\n"
    text += f"• Активных менторов: {active_mentors}\n\n"
    
    text += "📅 **Мероприятия:**\n"
    text += f"• Всего активных: {active_events}\n"
    text += f"• Предстоящих: {future_events}\n"
    text += f"• Прошедших: {past_events}\n\n"
    
    text += "📚 **Лекции:**\n"
    text += f"• Всего лекций: {total_lectures}\n"
    if programming_count > 0:
        text += f"• Программирование: {programming_count}\n"
    if security_count > 0:
        text += f"• Кибербезопасность: {security_count}\n"
    if data_count > 0:
        text += f"• Data Science: {data_count}\n"
    if web_count > 0:
        text += f"• Web разработка: {web_count}\n"
    if mobile_count > 0:
        text += f"• Mobile разработка: {mobile_count}\n"
    
    text += "\n💼 **Работа:**\n"
    text += f"• Активных вакансий: {active_vacancies}\n\n"
    
    text += "🚀 **Проекты:**\n"
    text += f"• Всего активных: {active_projects}\n"
    if discussion_count > 0:
        text += f"• На обсуждении: {discussion_count}\n"
    if development_count > 0:
        text += f"• В разработке: {development_count}\n"
    if completed_count > 0:
        text += f"• Завершенных: {completed_count}\n"
    
    # Добавляем кнопки для более детальной статистики
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Детальная статистика", callback_data="detailed_stats")],
        [InlineKeyboardButton(text="📊 Статистика по дням", callback_data="daily_stats")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "detailed_stats")
async def show_detailed_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        # Статистика по регистрациям за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = await session.execute(
            select(User).where(User.created_at >= thirty_days_ago)
        )
        recent_users_count = len(recent_users.scalars().all())
        
        # Статистика по мероприятиям за последние 30 дней
        recent_events = await session.execute(
            select(Event).where(
                and_(Event.is_active == True, Event.date_time >= thirty_days_ago)
            )
        )
        recent_events_count = len(recent_events.scalars().all())
        
        # Статистика по лекциям за последние 30 дней
        recent_lectures = await session.execute(
            select(Lecture).where(Lecture.uploaded_at >= thirty_days_ago)
        )
        recent_lectures_count = len(recent_lectures.scalars().all())
        
        # Статистика по вакансиям за последние 30 дней
        recent_vacancies = await session.execute(
            select(Vacancy).where(Vacancy.posted_at >= thirty_days_ago)
        )
        recent_vacancies_count = len(recent_vacancies.scalars().all())
        
        # Статистика по проектам за последние 30 дней
        recent_projects = await session.execute(
            select(Project).where(Project.created_at >= thirty_days_ago)
        )
        recent_projects_count = len(recent_projects.scalars().all())
        
        # Топ-5 менторов по количеству мероприятий
        top_mentors = await session.execute(
            select(Mentor.name, Event.mentor_id)
            .join(Event)
            .where(Event.is_active == True)
            .group_by(Mentor.name, Event.mentor_id)
        )
        mentor_events = {}
        for mentor_name, mentor_id in top_mentors:
            mentor_events_count = await session.execute(
                select(Event).where(
                    and_(Event.mentor_id == mentor_id, Event.is_active == True)
                )
            )
            mentor_events[mentor_name] = len(mentor_events_count.scalars().all())
        
        # Сортируем менторов по количеству мероприятий
        sorted_mentors = sorted(mentor_events.items(), key=lambda x: x[1], reverse=True)[:5]
    
    text = "📈 **Детальная статистика (последние 30 дней)**\n\n"
    
    text += "📊 **Активность:**\n"
    text += f"• Новых пользователей: {recent_users_count}\n"
    text += f"• Новых мероприятий: {recent_events_count}\n"
    text += f"• Новых лекций: {recent_lectures_count}\n"
    text += f"• Новых вакансий: {recent_vacancies_count}\n"
    text += f"• Новых проектов: {recent_projects_count}\n\n"
    
    if sorted_mentors:
        text += "🏆 **Топ менторов по мероприятиям:**\n"
        for i, (mentor_name, count) in enumerate(sorted_mentors, 1):
            text += f"{i}. {mentor_name}: {count} мероприятий\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К общей статистике", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "daily_stats")
async def show_daily_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        # Статистика за сегодня
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        today_users = await session.execute(
            select(User).where(
                and_(User.created_at >= today, User.created_at < tomorrow)
            )
        )
        today_users_count = len(today_users.scalars().all())
        
        today_events = await session.execute(
            select(Event).where(
                and_(Event.date_time >= today, Event.date_time < tomorrow, Event.is_active == True)
            )
        )
        today_events_count = len(today_events.scalars().all())
        
        today_lectures = await session.execute(
            select(Lecture).where(
                and_(Lecture.uploaded_at >= today, Lecture.uploaded_at < tomorrow)
            )
        )
        today_lectures_count = len(today_lectures.scalars().all())
        
        today_vacancies = await session.execute(
            select(Vacancy).where(
                and_(Vacancy.posted_at >= today, Vacancy.posted_at < tomorrow)
            )
        )
        today_vacancies_count = len(today_vacancies.scalars().all())
        
        today_projects = await session.execute(
            select(Project).where(
                and_(Project.created_at >= today, Project.created_at < tomorrow)
            )
        )
        today_projects_count = len(today_projects.scalars().all())
        
        # Статистика за вчера
        yesterday = today - timedelta(days=1)
        
        yesterday_users = await session.execute(
            select(User).where(
                and_(User.created_at >= yesterday, User.created_at < today)
            )
        )
        yesterday_users_count = len(yesterday_users.scalars().all())
        
        # Статистика за неделю
        week_ago = today - timedelta(days=7)
        
        week_users = await session.execute(
            select(User).where(User.created_at >= week_ago)
        )
        week_users_count = len(week_users.scalars().all())
        
        week_events = await session.execute(
            select(Event).where(
                and_(Event.date_time >= week_ago, Event.is_active == True)
            )
        )
        week_events_count = len(week_events.scalars().all())
    
    text = "📊 **Статистика по дням**\n\n"
    
    text += "📅 **Сегодня:**\n"
    text += f"• Новых пользователей: {today_users_count}\n"
    text += f"• Мероприятий: {today_events_count}\n"
    text += f"• Новых лекций: {today_lectures_count}\n"
    text += f"• Новых вакансий: {today_vacancies_count}\n"
    text += f"• Новых проектов: {today_projects_count}\n\n"
    
    text += "📅 **Вчера:**\n"
    text += f"• Новых пользователей: {yesterday_users_count}\n\n"
    
    text += "📅 **За неделю:**\n"
    text += f"• Новых пользователей: {week_users_count}\n"
    text += f"• Мероприятий: {week_events_count}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К общей статистике", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить ментора", callback_data="admin_add_mentor")],
        [InlineKeyboardButton(text="➖ Удалить ментора", callback_data="admin_remove_mentor")],
        [InlineKeyboardButton(text="📅 Добавить мероприятие", callback_data="admin_add_event")],
        [InlineKeyboardButton(text="✏️ Редактировать мероприятие", callback_data="admin_edit_event")],
        [InlineKeyboardButton(text="🗑 Удалить мероприятие", callback_data="admin_delete_event")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])
    
    await callback.message.edit_text("🔧 **Панель администратора**", reply_markup=keyboard, parse_mode="Markdown")

# 9. main.py
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

# 10. Инструкции по запуску:

"""
1. Создайте папку проекта и файловую структуру:
    it_jamaate_bot/
    ├── requirements.txt
    ├── .env
    ├── Dockerfile
    ├── docker-compose.yml
    └── app
        ├── main.py
        ├── database/
        │   ├── __init__.py
        │   ├── models.py
        │   └── database.py
        └── handlers/
            ├── __init__.py
            ├── user_handlers.py
            └── admin_handlers.py
"""
