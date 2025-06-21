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
from datetime import datetime


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
    
    await callback.message.edit_text("📅 Введите название мероприятия:")
    await state.set_state(AdminStates.event_title)

@admin_router.message(AdminStates.event_title)
async def get_event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Введите описание мероприятия:")
    await state.set_state(AdminStates.event_description)

@admin_router.message(AdminStates.event_description)
async def get_event_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("⏰ Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ:")
    await state.set_state(AdminStates.event_datetime)

@admin_router.message(AdminStates.event_datetime)
async def get_event_datetime(message: Message, state: FSMContext):
    try:
        event_datetime = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        await state.update_data(datetime=event_datetime)
        await message.answer("📍 Введите место проведения:")
        await state.set_state(AdminStates.event_location)
    except ValueError:
        await message.answer("❌ Неверный формат! Используйте ДД.ММ.ГГГГ ЧЧ:ММ")

@admin_router.message(AdminStates.event_location)
async def save_event(message: Message, state: FSMContext):
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        # Получаем пользователя
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one()
        
        event = Event(
            title=data['title'],
            description=data['description'],
            date_time=data['datetime'],
            location=message.text,
            created_by=user.id
        )
        session.add(event)
        await session.commit()
    
    await message.answer(f"✅ Мероприятие **{data['title']}** успешно добавлено!", parse_mode="Markdown")
    await state.clear()

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
                callback_data=f"edit_event_{event.id}"
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

@admin_router.callback_query(F.data.startswith("edit_event_"))
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
        [InlineKeyboardButton(text="◀️ К списку мероприятий", callback_data="admin_edit_event")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@admin_router.callback_query(F.data.startswith("edit_title_"))
async def edit_event_title(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[-1])
    await state.update_data(editing_event_id=event_id)
    await callback.message.edit_text("📝 Введите новое название мероприятия:")
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
    await callback.message.edit_text("📄 Введите новое описание мероприятия:")
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
    await callback.message.edit_text("⏰ Введите новую дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ:")
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
    await callback.message.edit_text("📍 Введите новое место проведения:")
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
