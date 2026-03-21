from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone, timedelta
import asyncio
import requests
import random
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

users = set()

RECIPES = [
    "🍽️ Խաշ\nԲաղադրատոմս՝ Եփել տավարի ոտքերը 6-8 ժամ, ավելացնել սխտոր, աղ։ Մատուցել լավաշով։",
    "🍽️ Դոլմա\nԲաղադրատոմս՝ Խառնել աղացած միս, բրինձ, սոխ, համեմ։ Փաթաթել խաղողի տերևով, եփել 40 րոպե։",
    "🍽️ Հարիսա\nԲաղադրատոմս՝ Եփել հավ և ցորեն 3-4 ժամ, անընդհատ խառնել մինչև շիլայի վերածվի։",
    "🍽️ Բաստուրմա\nԲաղադրատոմս՝ Տավարի միս պատել չաման համեմով, չորացնել 2-3 շաբաթ։",
    "🍽️ Ղափամա\nԲաղադրատոմս՝ Դատարկել դդումը, լցնել բրինձ, չամիչ, չորացրած մրգեր, թխել 2 ժամ։",
    "🍽️ Ժենգյալով հաց\nԲաղադրատոմս՝ Բարակ խմոր, մեջը լցնել 10+ տեսակ կանաչի, թխել տապակի վրա։",
    "🍽️ Քյուֆթա\nԲաղադրատոմս՝ Աղացած տավարի միս խառնել սոխ, համեմ, ձու։ Մեծ գնդիկներ պատրաստել, եփել արգանակի մեջ։",
]

FROM_CUR, TO_CUR, AMOUNT = range(3)
REMIND_DAY, REMIND_TIME, REMIND_TEXT = range(3, 6)
CURRENCIES = [["AMD", "USD", "EUR"], ["RUB", "GBP", "JPY"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.message.chat_id)
    await update.message.reply_text("Բարև! Ես բոտ եմ 🤖\nՕգտագործիր /help հրամանը։\n\nԱմեն օր կստանաս՝\n☀️ Երևանի եղանակը\n🍽️ Հայկական ուտեստի բաղադրատոմս")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Հրամաններ:\n/start - Սկսել\n/help - Օգնություն\n/about - Բոտի մասին\n/weather - Եղանակ\n/rate - Փոխարժեք\n/convert - Փոխարկել\n/remind - Հիշեցում")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ես Python-ով գրված Telegram բոտ եմ 🐍")

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Գրեք քաղաքի անունը։ Օրինակ՝ /weather Yerevan")
        return
    city = " ".join(context.args)
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url).json()
    if response.get("cod") != 200:
        await update.message.reply_text("Քաղաքը չգտնվեց։ Փորձեք անգլերենով։")
        return
    temp = response["main"]["temp"]
    desc = response["weather"][0]["description"]
    await update.message.reply_text(f"🌤 {city}\nՋերմաստիճան՝ {temp}°C\nԵղանակ՝ {desc}")

async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url).json()
    amd = response["rates"]["AMD"]
    eur = response["rates"]["EUR"]
    rub = response["rates"]["RUB"]
    await update.message.reply_text(f"💱 Փոխարժեք (USD)\n🇦🇲 1 USD = {amd} AMD\n🇪🇺 1 USD = {eur:.2f} EUR\n🇷🇺 1 USD = {rub:.2f} RUB")

async def convert_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(CURRENCIES, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("💱 Ո՞ր արժույթից ես փոխարկում։", reply_markup=reply_markup)
    return FROM_CUR

async def from_cur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["from_cur"] = update.message.text.upper()
    reply_markup = ReplyKeyboardMarkup(CURRENCIES, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Ո՞ր արժույթի փոխարկեմ։", reply_markup=reply_markup)
    return TO_CUR

async def to_cur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["to_cur"] = update.message.text.upper()
    await update.message.reply_text("Ի՞նչ գումար։", reply_markup=ReplyKeyboardRemove())
    return AMOUNT

async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amt = float(update.message.text.replace(",", ""))
        from_c = context.user_data["from_cur"]
        to_c = context.user_data["to_cur"]
        url = f"https://api.exchangerate-api.com/v4/latest/{from_c}"
        response = requests.get(url).json()
        rate = response["rates"].get(to_c)
        if not rate:
            await update.message.reply_text("Արժույթը չգտնվեց։")
            return ConversationHandler.END
        result = amt * rate
        await update.message.reply_text(f"💱 {amt:,.0f} {from_c} = {result:,.2f} {to_c}")
    except:
        await update.message.reply_text("Սխալ թիվ։ Փորձեք նորից /convert")
    return ConversationHandler.END

async def remind_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📅 Ո՞ր օրը։ (օրինակ՝ 21.03.2026)")
    return REMIND_DAY

async def remind_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["remind_day"] = update.message.text
    await update.message.reply_text("🕐 Ո՞ր ժամը։ (օրինակ՝ 14:30)")
    return REMIND_TIME

async def remind_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["remind_time"] = update.message.text
    await update.message.reply_text("📝 Ի՞նչ հիշեցնեմ։")
    return REMIND_TEXT

async def remind_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        day = context.user_data["remind_day"]
        time_str = context.user_data["remind_time"]
        text = update.message.text
        chat_id = update.message.chat_id
        tz = timezone(timedelta(hours=4))
        run_date = datetime.strptime(f"{day} {time_str}", "%d.%m.%Y %H:%M").replace(tzinfo=tz)
        now = datetime.now(tz)
        delay = (run_date - now).total_seconds()

        if delay <= 0:
            await update.message.reply_text("❌ Այդ ժամը արդեն անցել է։ Փորձեք ապագա ժամ։")
            return ConversationHandler.END

        async def send_reminder():
            await asyncio.sleep(delay)
            await context.bot.send_message(chat_id=chat_id, text=f"🔔 {text}")

        asyncio.create_task(send_reminder())
        await update.message.reply_text(f"✅ Կհիշեցնեմ {day}-ին ժամը {time_str}-ին՝ {text}")
    except:
        await update.message.reply_text("Սխալ։ Փորձեք նորից /remind")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Չեղարկվեց։", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def send_daily_weather(bot):
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Yerevan&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url).json()
    temp = response["main"]["temp"]
    desc = response["weather"][0]["description"]
    text = f"☀️ Բարի առավոտ!\n\nԵրևանի եղանակը՝\nՋերմաստիճան՝ {temp}°C\nԵղանակ՝ {desc}"
    for chat_id in users:
        try:
            await bot.send_message(chat_id=chat_id, text=text)
        except:
            pass

async def send_daily_recipe(bot):
    recipe = random.choice(RECIPES)
    for chat_id in users:
        try:
            await bot.send_message(chat_id=chat_id, text=recipe)
        except:
            pass

async def post_init(application):
    scheduler = AsyncIOScheduler(timezone="Asia/Yerevan")
    scheduler.add_job(send_daily_weather, "cron", hour=9, minute=0, args=[application.bot])
    scheduler.add_job(send_daily_recipe, "cron", hour=12, minute=0, args=[application.bot])
    scheduler.start()

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Հրամանը չճանաչվեց։ Օգտագործիր /help 😊")

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("convert", convert_start)],
    states={
        FROM_CUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, from_cur)],
        TO_CUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, to_cur)],
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

remind_handler = ConversationHandler(
    entry_points=[CommandHandler("remind", remind_start)],
    states={
        REMIND_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_day)],
        REMIND_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_time)],
        REMIND_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_text)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("rate", rate))
app.add_handler(conv_handler)
app.add_handler(remind_handler)
app.add_handler(MessageHandler(filters.TEXT, message))
app.run_polling()








