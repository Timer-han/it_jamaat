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
    
    # Добавляем время обновления для избежания дублирования контента
    current_time = datetime.now().strftime("%H:%M")
    
    if not events:
        # Добавляем кнопки навигации даже когда нет событий
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="events")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
        ])
        text = f"📅 Пока нет запланированных мероприятий\n\n🕐 Обновлено: {current_time}"
        try:
            await callback.message.edit_text(text, reply_markup=back_keyboard)
        except Exception:
            # Если не удалось отредактировать, отправляем ответ
            await callback.answer("📅 Список мероприятий обновлен")
        return
    
    text = f"📅 **Ближайшие мероприятия:**\n\n"
    for event in events:
        mentor_name = event.mentor.name if event.mentor else "Не указан"
        text += f"🔸 **{event.title}**\n"
        text += f"📍 {event.location or 'Онлайн'}\n"
        text += f"⏰ {event.date_time.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"👨‍🏫 {mentor_name}\n"
        if event.description:
            text += f"📝 {event.description[:100]}...\n"
        text += "\n"
    
    text += f"🕐 Обновлено: {current_time}"
    
    # Добавляем кнопку обновления списка
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="events")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")
    except Exception:
        # Если не удалось отредактировать, отправляем ответ
        await callback.answer("📅 Список мероприятий обновлен")

@router.callback_query(F.data == "mentors")
async def show_mentors(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Mentor).where(Mentor.is_active == True)
        )
        mentors = result.scalars().all()
    
    # Добавляем время обновления для избежания дублирования контента
    current_time = datetime.now().strftime("%H:%M")
    
    if not mentors:
        # Добавляем кнопки навигации даже когда нет менторов
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="mentors")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
        ])
        text = f"👨‍🏫 Пока нет активных менторов\n\n🕐 Обновлено: {current_time}"
        try:
            await callback.message.edit_text(text, reply_markup=back_keyboard)
        except Exception:
            await callback.answer("👨‍🏫 Список менторов обновлен")
        return
    
    text = f"👨‍🏫 **Наши менторы:**\n\n"
    for mentor in mentors:
        text += f"🔸 **{mentor.name}**\n"
        text += f"💼 {mentor.specialization or 'Специализация не указана'}\n"
        if mentor.bio:
            text += f"📝 {mentor.bio[:100]}...\n"
        if mentor.contact_info:
            text += f"📞 {mentor.contact_info}\n"
        text += "\n"
    
    text += f"🕐 Обновлено: {current_time}"
    
    # Добавляем кнопку обновления списка
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="mentors")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")
    except Exception:
        await callback.answer("👨‍🏫 Список менторов обновлен")

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
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "📚 **Выберите категорию лекций:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("lectures_"))
async def show_lectures_by_category(callback: CallbackQuery):
    category = callback.data.replace("lectures_", "")
    
    # Добавляем время обновления для избежания дублирования контента
    current_time = datetime.now().strftime("%H:%M")
    
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
    
    category_map = {
        "programming": "Программирование",
        "security": "Кибербезопасность", 
        "data": "Data Science",
        "web": "Web разработка",
        "mobile": "Mobile разработка"
    }
    
    if not lectures:
        # Улучшенная навигация для пустого списка лекций
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"lectures_{category}")],
            [InlineKeyboardButton(text="◀️ К категориям", callback_data="lectures")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
        ])
        text = f"📚 В данной категории пока нет лекций\n\n🕐 Обновлено: {current_time}"
        try:
            await callback.message.edit_text(text, reply_markup=back_keyboard)
        except Exception:
            await callback.answer("📚 Список лекций обновлен")
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
    
    text += f"🕐 Обновлено: {current_time}"
    
    # Улучшенная навигация с кнопкой обновления
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"lectures_{category}")],
        [InlineKeyboardButton(text="◀️ К категориям", callback_data="lectures")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")
    except Exception:
        await callback.answer("📚 Список лекций обновлен")

@router.callback_query(F.data == "vacancies")
async def show_vacancies(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Vacancy).where(Vacancy.is_active == True).order_by(Vacancy.posted_at.desc())
        )
        vacancies = result.scalars().all()
    
    # Добавляем время обновления для избежания дублирования контента
    current_time = datetime.now().strftime("%H:%M")
    
    if not vacancies:
        # Добавляем кнопки навигации даже когда нет вакансий
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="vacancies")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
        ])
        text = f"💼 Пока нет активных вакансий\n\n🕐 Обновлено: {current_time}"
        try:
            await callback.message.edit_text(text, reply_markup=back_keyboard)
        except Exception:
            await callback.answer("💼 Список вакансий обновлен")
        return
    
    text = f"💼 **Актуальные вакансии:**\n\n"
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
    
    text += f"🕐 Обновлено: {current_time}"
    
    # Добавляем кнопку обновления списка
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="vacancies")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")
    except Exception:
        await callback.answer("💼 Список вакансий обновлен")

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
    
    # Добавляем время обновления для избежания дублирования контента
    current_time = datetime.now().strftime("%H:%M")
    
    if not projects:
        # Добавляем кнопки навигации даже когда нет проектов
        back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="projects")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
        ])
        text = f"🚀 Пока нет активных проектов\n\n🕐 Обновлено: {current_time}"
        try:
            await callback.message.edit_text(text, reply_markup=back_keyboard)
        except Exception:
            await callback.answer("🚀 Список проектов обновлен")
        return
    
    text = f"🚀 **Активные проекты:**\n\n"
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
    
    text += f"🕐 Обновлено: {current_time}"
    
    # Добавляем кнопку обновления списка
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="projects")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=back_keyboard, parse_mode="Markdown")
    except Exception:
        await callback.answer("🚀 Список проектов обновлен")

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

# Дополнительный обработчик для команды /menu (для быстрого возврата к главному меню)
@router.message(Command("menu"))
async def menu_command(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Мероприятия", callback_data="events")],
        [InlineKeyboardButton(text="👨‍🏫 Менторы", callback_data="mentors")],
        [InlineKeyboardButton(text="📚 Лекции", callback_data="lectures")],
        [InlineKeyboardButton(text="💼 Вакансии", callback_data="vacancies")],
        [InlineKeyboardButton(text="🚀 Проекты", callback_data="projects")]
    ])
    
    await message.answer(
        "🕌💻 **IT Jama'at**\n\n"
        "Выберите интересующий раздел:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )