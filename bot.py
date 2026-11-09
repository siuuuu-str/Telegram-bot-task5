import asyncio
import logging
import sqlite3
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

# ВСТАВЬ СВОЙ ТОКЕН И СВОЙ ID
TOKEN = "9259216256:AAEqlZ0fvK_gzX5nzUnPg_xVjK6Fahcm-TU"
ADMIN_ID = 1121620411

logging.basicConfig(level=logging.INFO)
session = AiohttpSession()
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    # Таблица пользователей
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, registered_at TEXT)""")
    # Таблица истории команд
    cur.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, command TEXT, timestamp TEXT)""")
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (id, username, first_name, registered_at) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def log_command(user_id, command):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO history (user_id, command, timestamp) VALUES (?, ?, ?)",
                (user_id, command, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# --- КОМАНДЫ ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я запоминаю пользователей.\n\nКоманды:\n/stats - статистика\n/profile - твой профиль\n/users - список (только для админа)")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM history")
    commands_count = cur.fetchone()[0]
    conn.close()
    await message.answer(f"📊 Статистика:\n👥 Пользователей: {users_count}\n⚙️ Команд выполнено: {commands_count}")

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    
    # Информация о юзере
    cur.execute("SELECT registered_at FROM users WHERE id=?", (message.from_user.id,))
    reg_date = cur.fetchone()[0]
    
    # Количество его действий
    cur.execute("SELECT COUNT(*) FROM history WHERE user_id=?", (message.from_user.id,))
    actions = cur.fetchone()[0]
    conn.close()
    
    await message.answer(f"👤 Твой профиль:\nИмя: {message.from_user.first_name}\nДата регистрации: {reg_date}\nТвоих действий: {actions}")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет прав для этой команды.")
        return
        
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("SELECT id, username, first_name FROM users")
    users = cur.fetchall()
    conn.close()
    
    text = "👥 Список пользователей:\n"
    for u in users:
        text += f"ID: {u[0]} | @{u[1]} | {u[2]}\n"
    
    await message.answer(text)

@dp.message()
async def log_all_messages(message: types.Message):
    # Добавляем пользователя (если его еще нет)
    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    # Записываем команду в историю
    log_command(message.from_user.id, message.text)

async def main():
    init_db() # Создаем базу при запуске
    print("Бот с БД запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())