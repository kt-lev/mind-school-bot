from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import pytz, json
from pathlib import Path
from utils import check_file

user_router = Router()

class UserStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_number = State()
    waiting_for_question = State()

@user_router.message(Command('start'))
async def start(message: Message) -> None:
    btn1 = KeyboardButton(text="Напрямки та послуги центру розвитку")
    btn2 = KeyboardButton(text="Задати своє питання")
    btn3 = KeyboardButton(text="Про нас")
    markup = ReplyKeyboardMarkup(keyboard=[[btn1], [btn2, btn3]], resize_keyboard=True)
    await message.answer("Привіт, обери пункт", reply_markup=markup)

@user_router.message(F.text == "Напрямки та послуги центру розвитку")
async def show_services(message: Message) -> None:
    content = check_file('services.json')
    buttons = []
    for posluga in content:
        button = [InlineKeyboardButton(text=posluga["Name"], url=posluga["Url"])]
        buttons.append(button)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Ось наші послуги, натисніть на те, що зацікавило, щоб дізнатися більше", reply_markup=markup)

@user_router.message(F.text == "Про нас")
async def show_about_us(message: Message) -> None:
    about_us = check_file('about_us.json')
    about_us_text = (
        f"{about_us['Опис']}\n\n"
        f"Години роботи:\n{about_us['Години роботи']}\n\n"
        f"Контакти: {about_us['Контакти']}\n\n"
        f"Наш веб-сайт: {about_us['Посилання на вебсайт']}\n\n"
        f"Адреса: [{about_us['Адреса']}]({about_us['Посилання на Google Maps']})"
    )
    await message.answer(about_us_text, parse_mode='Markdown')
    await message.answer_location(latitude=50.36134631320339, longitude=30.407647045843753)

@user_router.message(F.text == "Задати своє питання")
async def ask_question(message: Message, state: FSMContext) -> None:
    await message.answer("Введіть ім'я:")
    await state.set_state(UserStates.waiting_for_name)

@user_router.message(UserStates.waiting_for_name)
async def get_user_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await message.answer("Введіть номер телефону:")
    await state.set_state(UserStates.waiting_for_number)

@user_router.message(UserStates.waiting_for_number)
async def get_user_number(message: Message, state: FSMContext) -> None:
    await state.update_data(number=message.text)
    await message.answer("Напишіть Ваше питання:")
    await state.set_state(UserStates.waiting_for_question)

@user_router.message(UserStates.waiting_for_question)
async def process_question(message: Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    user_name = state_data.get('name')
    user_number = state_data.get('number')
    question = message.text
    user_nickname = message.from_user.username
    question_time = datetime.now(pytz.timezone("Europe/Kiev")).strftime("%d.%m.%Y %H:%M:%S")

    data = check_file('questions.json')
    person = {
        "Name": user_name,
        "Number": user_number,
        "Question": question,
        "Username": user_nickname,
        "Time": question_time
    }
    data.append(person)

    questions_path = Path('../mind_bot/json/questions.json')
    with open(questions_path, 'w', encoding='utf-8') as in_questions:
        json.dump(data, in_questions, ensure_ascii=False, indent=4)

    await message.answer("Дякую за ваше питання! Ми з вами зв'яжемося найближчим часом.")
    await state.clear()

    admins = check_file('admins.json')
    admin_id = admins['Admin Id-number']
    from app.main import bot
    await bot.send_message(admin_id, f"Нове запитання!\nВід: {user_name} (@{user_nickname})\nНомер телефону: {user_number}\nНадіслали о: {question_time}\nПитання: {question}")
