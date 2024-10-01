from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sqlite3
from utils import is_admin

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_posluga_name = State()
    waiting_for_posluga_description = State()
    waiting_for_about_us = State()
    waiting_for_new_posluga_name = State()
    waiting_for_new_posluga_url = State()
    waiting_for_delete_posluga_name = State()

conn = sqlite3.connect('db/database.db')
cursor = conn.cursor()

@admin_router.message(Command('admin'))
async def admin(message: Message, state: FSMContext) -> None:
    if is_admin(message.chat.id):
        btn1 = KeyboardButton(text='Редагувати послуги')
        btn2 = KeyboardButton(text='Редагувати "Про нас"')
        markup = ReplyKeyboardMarkup(keyboard=[[btn1, btn2]], resize_keyboard=True)
        await state.update_data(menu_state = markup)
        await message.answer("Адмін режим активовано", reply_markup=markup)
    else:
        await message.answer("Ви не маєте доступу до функцій адміністратора!")

@admin_router.callback_query(F.data == "rename")
async def callback_rename_service(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Введіть нову назву:")
    await state.set_state(AdminStates.waiting_for_posluga_name)

@admin_router.callback_query(F.data == "rewrite")
async def callback_edit_service_description(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Вставте нове URL-посилання на описову сторінку:")
    await state.set_state(AdminStates.waiting_for_posluga_description)

@admin_router.callback_query(F.data.in_({"Опис", "Години роботи", "Адресу", "Контакти", "Посилання на вебсайт", "Посилання на Google Maps"}))
async def edit_about_us_field(call: CallbackQuery, state: FSMContext):
    fields = {
        "Опис": "description",
        "Години роботи": "schedule",
        "Адресу": "address",
        "Контакти": "contact_num",
        "Посилання на вебсайт": "link_on_website",
        "Посилання на Google Maps": "link_on_google_maps"
    }
    field_prompts = {
        "Опис": "Введіть новий опис:",
        "Години роботи": "Введіть новий час роботи:",
        "Адресу": "Введіть нову адресу:",
        "Контакти": "Введіть нові контакти:",
        "Посилання на вебсайт": "Введіть новий вебсайт:",
        "Посилання на Google Maps": "Введіть нове посилання на Google Maps:"
    }
    await call.message.answer(text=f"{field_prompts[call.data]}")
    await state.update_data(field=f"{fields[call.data]}")
    await state.set_state(AdminStates.waiting_for_about_us)

@admin_router.callback_query(F.data)
async def select_service(call: CallbackQuery, state: FSMContext):
    id = int(call.data)
    cursor.execute(f"SELECT Name FROM services WHERE Id = {id}")
    name = cursor.fetchone()
    await state.update_data(flag_id=id)
    btn1 = InlineKeyboardButton(text="Змінити назву", callback_data="rename")
    btn2 = InlineKeyboardButton(text="Змінити опис", callback_data="rewrite")
    markup = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])
    await call.message.answer(text=f"Ви обрали послугу: {name[0]}", reply_markup=markup)

@admin_router.message(F.text == 'Редагувати послуги')
async def edit_services(message: Message):
    if is_admin(message.chat.id):
        btn1 = KeyboardButton(text="Додати послугу")
        btn2 = KeyboardButton(text="Видалити послугу")
        btn3 = KeyboardButton(text="Повернутися")
        markup1 = ReplyKeyboardMarkup(keyboard=[[btn1, btn2], [btn3]], resize_keyboard=True)

        cursor.execute("SELECT * FROM services")
        data = cursor.fetchall()
        buttons = []
        for posluga in data:
            name = posluga[1]
            id = posluga[0]
            button = InlineKeyboardButton(text=name, callback_data=str(id))
            buttons.append([button])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer("Щоб редагувати якісь з вже існуючих послуг, оберіть із запропонованих:", reply_markup=markup)
        await message.answer("Для того щоб додати нову послугу або видалити якусь із існуючих, оберіть необхідну дію тут:", reply_markup=markup1)

@admin_router .message(F.text == 'Редагувати "Про нас"')
async def menu_edit_about_us(message: Message):
    if is_admin(message.chat.id):
        buttons = []
        about_us = ["Опис", "Години роботи", "Адресу", "Контакти", "Посилання на вебсайт", "Посилання на Google Maps"]
        for field in about_us:
            button = InlineKeyboardButton(text=f"Редагувати {field}", callback_data=field)
            buttons.append([button])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("Виберіть, що саме ви хочете редагувати:", reply_markup=markup)

@admin_router.message(F.text == 'Повернутися')
async def back_to_menu(message: Message, state: FSMContext):
    if is_admin(message.chat.id):
        menu_state = (await state.get_data())['menu_state']
        if menu_state:
            await message.answer('Ви повернулися в головне меню!', reply_markup=menu_state)
        else:
            await message.answer('Помилка повернення до головного меню!')

@admin_router.message(F.text == 'Додати послугу')
async def add_service(message: Message, state: FSMContext):
    if is_admin(message.chat.id):
        await message.answer("Введіть назву нової послуги:")
        await state.set_state(AdminStates.waiting_for_new_posluga_name)

@admin_router.message(F.text == 'Видалити послугу')
async def delete_service(message: Message, state: FSMContext):
    if is_admin(message.chat.id):
        await message.answer("Введіть назву послуги, яку хочете видалити:")
        await state.set_state(AdminStates.waiting_for_delete_posluga_name)

@admin_router.message(AdminStates.waiting_for_posluga_name)
async def edit_service_name(message: Message, state: FSMContext):
    state_data = await state.get_data()
    flag_id = state_data.get('flag_id')
    cursor.execute("UPDATE services SET Name = ? WHERE Id = ?", (message.text, flag_id))
    conn.commit()
    await message.answer(f"Назву успішно змінено на: {message.text}!")
    

@admin_router.message(AdminStates.waiting_for_posluga_description)
async def edit_service_description(message: Message, state: FSMContext):
    state_data = await state.get_data()
    flag_id = state_data.get('flag_id')
    cursor.execute("UPDATE services SET Url = ? WHERE Id = ?", (message.text, flag_id))
    conn.commit()
    await message.answer(f"Опис успішно змінено на: {message.text}")
    

@admin_router.message(AdminStates.waiting_for_about_us)
async def edit_about_us(message: Message, state: FSMContext):
    state_data = await state.get_data()
    field_about_us = state_data.get('field')
    cursor.execute(f"UPDATE about_us SET {field_about_us} = ? WHERE id = 1", (message.text,))
    conn.commit()
    field_name = {
        "description": "Опис",
        "schedule": "Години роботи",
        "address": "Адресу",
        "contact_num": "Контакти",
        "link_on_website": "Посилання на вебсайт",
        "link_on_google_maps": "Посилання на Google Maps"
    }
    await message.answer(f"{field_name[field_about_us]} успішно змінено на: {message.text}")
    

@admin_router.message(AdminStates.waiting_for_new_posluga_name)
async def add_new_service_name(message: Message, state: FSMContext):
    await message.answer("Введіть URL-посилання на описову сторінку послуги:")
    await state.update_data(new_posluga_name=message.text)
    await state.set_state(AdminStates.waiting_for_new_posluga_url)

@admin_router.message(AdminStates.waiting_for_new_posluga_url)
async def add_new_service_url(message: Message, state: FSMContext):
    state_data = await state.get_data()
    new_posluga_name = state_data.get('new_posluga_name')
    cursor.execute("INSERT INTO services (Name, Url) VALUES (?, ?)", (new_posluga_name, message.text))
    conn.commit()
    await message.answer(f"Послуга '{new_posluga_name}' успішно додана!")
    

@admin_router.message(AdminStates.waiting_for_delete_posluga_name)
async def delete_service_name(message: Message, state: FSMContext):
    cursor.execute("DELETE FROM services WHERE Name = ?", (message.text))
    conn.commit()
    await message.answer(f"Послуга '{message.text}' успішно видалена!")
    