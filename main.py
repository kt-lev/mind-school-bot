import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import json
import os
import pytz
from datetime import datetime

bot = Bot(token='7239649070:AAEVL4Hllh8rKLsmfMBHLYY6lUItt_KBTHY')
dp = Dispatcher()

flag_name = None
menu_state = None
action_state = {}

@dp.callback_query(lambda call: True)
async def callback_query_handler(call):
 await bot.answer_callback_query(call.id)
 global flag_name

 if call.data == "rename":
         await bot.send_message(call.message.chat.id, "Введіть нову назву:")
         action_state[call.message.chat.id] = {'state': 'waiting_for_posluga_name', 'posluga name': flag_name}
     
 elif call.data == "rewrite":
         await bot.send_message(call.message.chat.id, "Вставте нове URL-посилання на описову сторінку:")
         action_state[call.message.chat.id] = {'state': 'waiting_for_posluga_description', 'posluga name': flag_name}
         
 elif call.data in ["Опис", "Години роботи", "Адреса", "Контакти", "Посилання на вебсайт", "Посилання на Google Maps"]:
          field_prompts = {
            "Опис": "Введіть новий опис:",
            "Години роботи": "Введіть новий час роботи:",
            "Адреса": "Введіть нову адресу:",
            "Контакти": "Введіть нові контакти:",
            "Посилання на вебсайт": "Введіть новий вебсайт:",
            "Посилання на Google Maps": "Введіть нове посилання на Google Maps:"
          }
          await bot.send_message(call.message.chat.id, field_prompts[call.data])
          action_state[call.message.chat.id] = {'state': 'waiting_for_about_us', 'field': call.data}
 else:
      data = []
      with open('poslugy.json', 'r', encoding='utf-8') as file:
         data = json.load(file)
      for context in data:
         if call.data == context["Name"]:
             flag_name = call.data
             btn1 = InlineKeyboardButton(text = "Змінити назву", callback_data = "rename", )
             btn2 = InlineKeyboardButton(text = "Змінити опис", callback_data = "rewrite")
             markup = InlineKeyboardMarkup(inline_keyboard=[[btn1,btn2]])
             await bot.send_message(call.message.chat.id, f"Ви обрали послугу: {context.get("Name")}", reply_markup=markup)
             break

@dp.message(Command("start"))
async def start(message: Message) -> None:
    btn1 = KeyboardButton(text="Напрямки та послуги центру розвитку")
    btn2 = KeyboardButton(text="Задати своє питання")
    btn3 = KeyboardButton(text="Про нас")
    markup = ReplyKeyboardMarkup(keyboard=[[btn1], [btn2, btn3]], resize_keyboard=True)
    await bot.send_message(message.chat.id, "Привіт, обери пункт", reply_markup=markup)

@dp.message(Command('admin'))
async def admin(message: Message) -> None:
     global menu_state
     with open('admins.json', 'r', encoding='utf-8') as reply_by_admin:
        admins = json.load(reply_by_admin)
     if message.chat.id == admins["Admin Id-number"]:
        btn1 = KeyboardButton(text='Редагувати послуги')
        btn2 = KeyboardButton(text='Редагувати "Про нас"')
        markup = ReplyKeyboardMarkup(keyboard=[[btn1, btn2]], resize_keyboard=True)
        menu_state = markup
        await bot.send_message(message.chat.id, "Адмін режим активовано", reply_markup=markup)
     else: 
        await bot.send_message(message.chat.id, "Ви не маєте доступу до функцій адміністратора!")

@dp.message(F.content_type == 'text')
async def text(message: Message):
    global menu_state

    if message.text == 'Напрямки та послуги центру розвитку':
        buttons = []
        with open('poslugy.json', 'r', encoding='utf-8') as file:
            content = json.load(file)
            for posluga in content:
                name = posluga["Name"]
                base_url = posluga["Url"]
                button = InlineKeyboardButton(text=name, url=base_url)
                buttons.append([button])
            markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(message.chat.id, "Ось наші послуги, натисніть на те, що зацікавило, щоб дізнатися більше", reply_markup=markup)

    elif message.text == 'Про нас':
        with open('about_us.json', 'r', encoding='utf-8') as file:
            about_us = json.load(file)
        await bot.send_message(message.chat.id, f"{about_us['Опис']}\n\nГодини роботи:\n{about_us['Години роботи']}\n\nКонтакти: {about_us['Контакти']}\n\nНаш веб-сайт: {about_us['Посилання на вебсайт']}\n\nАдреса:[{about_us['Адреса']}]({about_us['Посилання на Google Maps']})", parse_mode='Markdown')
        await bot.send_location(message.chat.id, latitude=50.36134631320339, longitude=30.407647045843753)
    
    elif message.text == 'Задати своє питання':
        await bot.send_message(message.chat.id, "Введіть ім'я:")
        action_state[message.chat.id] = {'state': 'waiting_for_name'}
    
    elif message.text == 'Редагувати послуги':
        buttons = []
        btn1 = KeyboardButton(text = "Додати послугу")
        btn2 = KeyboardButton(text = "Видалити послугу")
        btn3 = KeyboardButton(text = "Повернутися")
        markup1 = ReplyKeyboardMarkup(keyboard = [[btn1, btn2],[btn3]], resize_keyboard=True)
        with open('poslugy.json', 'r', encoding='utf-8') as file:
            content = json.load(file)
            for posluga in content:
                name = posluga["Name"]
                button = InlineKeyboardButton(text=name, callback_data = name)
                buttons.append([button])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons) 
        await bot.send_message(message.chat.id, "Щоб редагувати якісь з вже існуючих полслуг оберіть із запропонованих:", reply_markup=markup)
        await bot.send_message(message.chat.id, "Для того щоб додати нову послугу, або видалити якусь із існуючих, оберіть необхідну дію тут:", reply_markup=markup1)

    elif message.text == 'Редагувати "Про нас"':
        buttons = []
        with open('about_us.json', 'r', encoding='utf-8') as file:
            about_us = json.load(file)
        for key in about_us.keys():
            button = InlineKeyboardButton(text=key, callback_data=key)
            buttons.append([button])
        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await bot.send_message(message.chat.id, "Виберіть що саме ви хочете редагувати:", reply_markup=markup)

    elif message.text == 'Повернутися':
        await bot.send_message(message.chat.id, 'Ви повернулися в головне меню!', reply_markup=menu_state)

    elif message.text == 'Додати послугу':
         await bot.send_message(message.chat.id, "Введіть назву нової послуги:")
         action_state[message.chat.id] = {'state': 'waiting_for_new_posluga_name'}

    elif message.text == 'Видалити послугу':
         await bot.send_message(message.chat.id, "Введіть назву послуги, яку хочете видалити:")
         action_state[message.chat.id] = {'state': 'waiting_for_delete_posluga_name'}

    else:
        state_info = action_state.get(message.chat.id)
        if state_info:
            state = state_info.get('state')
            posluga_name = state_info.get('posluga name')
            field_about_us = state_info.get('field')

            if state == 'waiting_for_name':
                name = message.text
                action_state[message.chat.id].update({'state': 'waiting_for_number', 'name': name})
                await bot.send_message(message.chat.id, "Введіть номер телефону:")

            elif state == 'waiting_for_number':
                number = message.text
                action_state[message.chat.id].update({'state': 'waiting_for_question', 'number': number})
                await bot.send_message(message.chat.id, "Напишіть Ваше питання:")

            elif state == 'waiting_for_question':
                question = message.text
                user_name = state_info.get('name')
                user_number = state_info.get('number')
                user_nickname = message.from_user.username
                question_time = datetime.now(pytz.timezone("Europe/Kiev")).strftime("%d.%m.%Y %H:%M:%S")
                if os.path.exists('questions.json'):
                     with open('questions.json', 'r', encoding='utf-8') as file:
                      try:
                         data = json.load(file)
                      except json.JSONDecodeError:
                         data = []
                else:
                      data = []

                person = {
                        "Name" : user_name,
                        "Number": user_number,
                        "Question" : question,
                        "Username" : user_nickname,
                        "Time" : question_time
                    }

                data.append(person)

                with open('questions.json', 'w', encoding='utf-8') as in_questions:
                        json.dump(data, in_questions, ensure_ascii=False, indent=4)

                await bot.send_message(message.chat.id, "Дякую за ваше питання! Ми з вами зв'яжемося найближчим часом.")
                action_state[message.chat.id] = None
                with open('admins.json', 'r', encoding='utf-8') as reply_by_admin:
                        admins = json.load(reply_by_admin)
                        if admins:
                               await bot.send_message(admins['Admin Id-number'], f"Нове запитання!\nВід: {user_name} (@{user_nickname})\nНомер телефону: {user_number}\nНадіслали о: {question_time}\nПитання: {question}")
            
            elif state == 'waiting_for_posluga_name':
                with open('poslugy.json', 'r', encoding='utf-8') as file:
                 data = json.load(file)

                for context in data:
                    if context["Name"] == posluga_name:
                        context["Name"] = message.text
    

                with open('poslugy.json', 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)
                await bot.send_message(message.chat.id, f"Назву успішно змінено на: {message.text}!")

            elif state == 'waiting_for_posluga_description':
                
             with open('poslugy.json', 'r', encoding='utf-8') as file:
                data = json.load(file)

                for context in data:
                    if context["Name"] == posluga_name:
                        context["Url"] = message.text
    
                with open('poslugy.json', 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)
                await bot.send_message(message.chat.id, f"Опис успішно змінено на: {message.text}")

            elif state == 'waiting_for_about_us':
                with open('about_us.json', 'r', encoding='utf-8') as file:
                  about_us = json.load(file)
                
                about_us[field_about_us] = message.text 

                with open('about_us.json', 'w', encoding='utf-8') as file:
                    json.dump(about_us, file, ensure_ascii=False, indent=4)
                
                if field_about_us == "Опис": 
                    field_name = "Опис"    
                elif field_about_us == "Години роботи":
                    field_name = "Години роботи"
                elif field_about_us == "Адреса":
                    field_name = "Адресу"
                elif field_about_us == "Контакти":
                    field_name = "Контакти"
                elif field_about_us == "Посилання на вебсайт":
                    field_name = "Посилання на вебсайт"
                elif field_about_us == "Посилання на Google Maps":
                    field_name = "Посилання на Google Maps"
                
                await bot.send_message(message.chat.id, f"{field_name} змінено на: {message.text}!")
            
            elif state == 'waiting_for_new_posluga_name':
                 await bot.send_message(message.chat.id, "Вставте URL опису послуги:")
                 action_state[message.chat.id] = {'state': 'waiting_for_new_posluga_url', 'name' : message.text}

            elif state == 'waiting_for_new_posluga_url':
                if os.path.exists('poslugy.json'):
                 with open('poslugy.json', 'r', encoding='utf-8') as file:
                  try:
                   data = json.load(file)
                  except json.JSONDecodeError:
                         data = []
                else:
                      data = []
                
                new_posluga = {
                    "Name" : state_info.get('name'),
                    "Url" : message.text
                }

                data.append(new_posluga)

                with open('poslugy.json', 'w', encoding='utf-8') as in_poslugy:
                        json.dump(data, in_poslugy, ensure_ascii=False, indent=4)
                
                await bot.send_message(message.chat.id, f"Додана нова послуга: {state_info.get('name')}!")

            elif state == 'waiting_for_delete_posluga_name':
                if os.path.exists('poslugy.json'):
                 with open('poslugy.json', 'r', encoding='utf-8') as file:
                  try:
                   data = json.load(file)
                  except json.JSONDecodeError:
                         data = []
                else:
                      data = []
                
                for posluga in data:
                    if posluga["Name"] == message.text:
                        data.remove(posluga)
                with open('poslugy.json', 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

                await bot.send_message(message.chat.id, f"Видалена послуга: {message.text}!")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
