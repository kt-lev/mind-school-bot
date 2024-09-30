from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
from pathlib import Path
from utils import check_file, is_admin

admin_router = Router()

class AdminStates(StatesGroup):
    waiting_for_posluga_name = State()
    waiting_for_posluga_description = State()
    waiting_for_about_us = State()
    waiting_for_new_posluga_name = State()
    waiting_for_new_posluga_url = State()
    waiting_for_delete_posluga_name = State()

@admin_router.message(Command('admin'))
async def admin(message: Message, state: FSMContext) -> None:
    if await is_admin(message.chat.id):
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

@admin_router.callback_query(F.data.in_({"Опис", "Години роботи", "Адреса", "Контакти", "Посилання на вебсайт", "Посилання на Google Maps"}))
async def edit_about_us_field(call: CallbackQuery, state: FSMContext):
    field_prompts = {
        "Опис": "Введіть новий опис:",
        "Години роботи": "Введіть новий час роботи:",
        "Адреса": "Введіть нову адресу:",
        "Контакти": "Введіть нові контакти:",
        "Посилання на вебсайт": "Введіть новий вебсайт:",
        "Посилання на Google Maps": "Введіть нове посилання на Google Maps:"
    }
    await call.message.answer(text=f"{field_prompts[call.data]}")
    await state.update_data(field=call.data)
    await state.set_state(AdminStates.waiting_for_about_us)

@admin_router.callback_query(F.data)
async def select_service(call: CallbackQuery, state: FSMContext):
    data = check_file('services.json')
    for context in data:
        if call.data == context["Name"]:
            await state.update_data(flag_name=call.data)
            btn1 = InlineKeyboardButton(text="Змінити назву", callback_data="rename")
            btn2 = InlineKeyboardButton(text="Змінити опис", callback_data="rewrite")
            markup = InlineKeyboardMarkup(inline_keyboard=[[btn1, btn2]])
            await call.message.answer(text=f"Ви обрали послугу: {context.get('Name')}", reply_markup=markup)
            break

@admin_router.message(F.text == 'Редагувати послуги', F.chat.id.func(is_admin))
async def edit_services(message: Message):
    buttons = []
    btn1 = KeyboardButton(text="Додати послугу")
    btn2 = KeyboardButton(text="Видалити послугу")
    btn3 = KeyboardButton(text="Повернутися")
    markup1 = ReplyKeyboardMarkup(keyboard=[[btn1, btn2], [btn3]], resize_keyboard=True)
    content = check_file('services.json')
    for posluga in content:
        name = posluga["Name"]
        button = InlineKeyboardButton(text=name, callback_data=name)
        buttons.append(button)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons) 
    await message.answer("Щоб редагувати якісь з вже існуючих послуг, оберіть із запропонованих:", reply_markup=markup)
    await message.answer("Для того щоб додати нову послугу або видалити якусь із існуючих, оберіть необхідну дію тут:", reply_markup=markup1)

@admin_router.message(F.text == 'Редагувати "Про нас"', F.chat.id.func(is_admin))
async def menu_edit_about_us(message: Message):
    buttons = []
    about_us = check_file('about_us.json')
    for key in about_us.keys():
        button = InlineKeyboardButton(text=key, callback_data=key)
        buttons.append([button])
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Виберіть, що саме ви хочете редагувати:", reply_markup=markup)

@admin_router.message(F.text == 'Повернутися', F.chat.id.func(is_admin))
async def back_to_menu(message: Message, state: FSMContext):
    menu_state = (await state.get_data()).get('menu_state')
    if menu_state:
        await message.answer('Ви повернулися в головне меню!', reply_markup=menu_state)
    else:
        await message.answer('Помилка повернення до головного меню!')

@admin_router.message(F.text == 'Додати послугу', F.chat.id.func(is_admin))
async def add_service(message: Message, state: FSMContext):
    await message.answer("Введіть назву нової послуги:")
    await state.set_state(AdminStates.waiting_for_new_posluga_name)

@admin_router.message(F.text == 'Видалити послугу', F.chat.id.func(is_admin))
async def delete_service(message: Message, state: FSMContext):
    await message.answer("Введіть назву послуги, яку хочете видалити:")
    await state.set_state(AdminStates.waiting_for_delete_posluga_name)

@admin_router.message(AdminStates.waiting_for_posluga_name)
async def edit_service_name(message: Message, state: FSMContext):
    data = check_file('services.json')
    state_data = await state.get_data()
    flag_name = state_data.get('flag_name')
    for context in data:
        if context["Name"] == flag_name:
            context["Name"] = message.text
    services_path = Path('../mind_bot/json/services.json')
    with open(services_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    await message.answer(f"Назву успішно змінено на: {message.text}!")
    await state.clear()

@admin_router.message(AdminStates.waiting_for_posluga_description)
async def edit_service_description(message: Message, state: FSMContext):
    data = check_file('services.json')
    state_data = await state.get_data()
    flag_name = state_data.get('flag_name')
    for context in data:
        if context["Name"] == flag_name:
            context["Url"] = message.text
    services_path = Path('../mind_bot/json/services.json')
    with open(services_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    await message.answer(f"Опис успішно змінено на: {message.text}")
    await state.clear()

@admin_router.message(AdminStates.waiting_for_about_us)
async def edit_about_us(message: Message, state: FSMContext):
    state_data = await state.get_data()
    field_about_us = state_data.get('field')
    about_us = check_file('about_us.json')
    about_us[field_about_us] = message.text 
    about_us_path = Path('../mind_bot/json/about_us.json')
    with open(about_us_path, 'w', encoding='utf-8') as file:
        json.dump(about_us, file, ensure_ascii=False, indent=4)
    field_name = {
        "Опис": "Опис",
        "Години роботи": "Години роботи",
        "Адреса": "Адресу",
        "Контакти": "Контакти",
        "Посилання на вебсайт": "Посилання на вебсайт",
        "Посилання на Google Maps": "Посилання на Google Maps"
    }[field_about_us]
    await message.answer(f"{field_name} змінено на: {message.text}!")
    await state.clear()

@admin_router.message(AdminStates.waiting_for_new_posluga_name)
async def new_service_name(message: Message, state: FSMContext):
    await message.answer("Вставте URL опису послуги:")
    await state.update_data(name=message.text)
    await state.set_state(AdminStates.waiting_for_new_posluga_url)

@admin_router.message(AdminStates.waiting_for_new_posluga_url)
async def new_service_url(message: Message, state: FSMContext):
    data = check_file('services.json')
    state_data = await state.get_data()
    name = state_data.get('name')
    data.append({"Name": name, "Url": message.text})
    services_path = Path('../mind_bot/json/services.json')
    with open(services_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    await message.answer(f"Нову послугу '{name}' успішно додано!")
    await state.clear()

@admin_router.message(AdminStates.waiting_for_delete_posluga_name)
async def delete_service_name(message: Message, state: FSMContext):
    data = check_file('services.json')
    for context in data:
        if context["Name"] == message.text:
            data.remove(context)
            services_path = Path('../mind_bot/json/services.json')
            with open(services_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            await message.answer(f"Послугу '{message.text}' успішно видалено!")
            break
    else:
        await message.answer(f"Послугу з назвою '{message.text}' не знайдено!")
    await state.clear()