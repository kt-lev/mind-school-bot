from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import pytz
import sqlite3

user_router = Router()

conn = sqlite3.connect('db/database.db')
cursor = conn.cursor()

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
    cursor.execute("SELECT Name, Url FROM services")
    services = cursor.fetchall()
    buttons = []
    for service in services:
        button = [InlineKeyboardButton(text=service[0], url=service[1])]
        buttons.append(button)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Ось наші послуги, натисніть на те, що зацікавило, щоб дізнатися більше", reply_markup=markup)

@user_router.message(F.text == "Про нас")
async def show_about_us(message: Message) -> None:
    cursor.execute("SELECT description, schedule, contact_num, link_on_website, address, link_on_google_maps FROM about_us WHERE id =1")
    about_us = cursor.fetchone()
    about_us_text = (
        f"{about_us[0]}\n\n"
        f"Години роботи:\n{about_us[1]}\n\n"
        f"Контакти: {about_us[2]}\n\n"
        f"Наш веб-сайт: {about_us[3]}\n\n"
        f"Адреса: [{about_us[4]}]({about_us[5]})"
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

    cursor.execute("INSERT INTO questions (Name, Number, Question, Username, Time) VALUES (?, ?, ?, ?, ?)", (user_name, user_number, question, user_nickname, question_time))
    conn.commit()

    await message.answer("Дякую за ваше питання! Ми з вами зв'яжемося найближчим часом.")
    await state.clear()

    cursor.execute("SELECT tg_id FROM admins WHERE id = 1")
    admin_id = cursor.fetchone()[0]
    from app.main import bot
    await bot.send_message(admin_id, f"Нове запитання!\nВід: {user_name} (@{user_nickname})\nНомер телефону: {user_number}\nНадіслали о: {question_time}\nПитання: {question}")
