from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiohttp
import asyncio
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

USERS_FILE = "users.json"
users = set()

# ---------------- USERS SAVE/LOAD ----------------

def load_users():
    global users
    try:
        with open(USERS_FILE) as f:
            users = set(json.load(f))
    except:
        users = set()

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    users.add(chat_id)
    save_users()
    await update.message.reply_text(
        "Բարև 👋\nԵս ամեն օր ժամը 09:00-ին կուղարկեմ Երևանի ամբողջ օրվա եղանակը ☀️"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - գրանցվել\n/help - օգնություն")

# ---------------- WEATHER (HOURLY) ----------------

async def get_hourly_weather():
    url = f"http://api.openweathermap.org/data/2.5/forecast?q=Yerevan&appid={WEATHER_API_KEY}&units=metric"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    if "list" not in data:
        return "❌ Չհաջողվեց ստանալ եղանակը"

    today = datetime.now().date()

    text = "☀️ Այսօրվա եղանակը Երևանում\n\n"

    for item in data["list"]:
        dt = datetime.fromtimestamp(item["dt"])
        if dt.date() != today:
            continue

        hour = dt.strftime("%H:%M")
        temp = item["main"]["temp"]
        desc = item["weather"][0]["description"]

        text += f"🕒 {hour} → {temp}°C, {desc}\n"

    return text

# ---------------- DAILY SENDER ----------------

async def send_daily_weather(bot):
    text = await get_hourly_weather()

    for chat_id in users.copy():
        try:
            await bot.send_message(chat_id=chat_id, text=text)
            await asyncio.sleep(0.1)  # anti-spam
        except Exception as e:
            print(f"Error {chat_id}: {e}")
            users.remove(chat_id)
            save_users()

# ---------------- SCHEDULER ----------------

async def post_init(application):
    scheduler = AsyncIOScheduler(timezone="Asia/Yerevan")

    scheduler.add_job(
        send_daily_weather,
        "cron",
        hour=9,
        minute=0,
        args=[application.bot]
    )

    scheduler.start()

# ---------------- MAIN ----------------

load_users()

app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))

app.run_polling()