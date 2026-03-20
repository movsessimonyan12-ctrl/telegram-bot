from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

scheduler = AsyncIOScheduler()

FROM_CUR, TO_CUR, AMOUNT = range(3)
CURRENCIES = [["AMD", "USD", "EUR"], ["RUB", "GBP", "JPY"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Բարև! Ես բոտ եմ 🤖\nՕգտագործիր /help հրամանը։")

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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Չեղարկվեց։", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Օրինակ՝ /remind 10 Զանգել բժշկին\n(10 - րոպե)")
        return
    try:
        minutes = int(context.args[0])
        text = " ".join(context.args[1:])
        chat_id = update.message.chat_id

        async def send_reminder():
            await context.bot.send_message(chat_id=chat_id, text=f"🔔 Հիշեցում՝ {text}")

        scheduler.add_job(send_reminder, "date", run_date=None, misfire_grace_time=60, id=str(chat_id))
        from datetime import datetime, timedelta
        run_time = datetime.now() + timedelta(minutes=minutes)
        scheduler.add_job(send_reminder, "date", run_date=run_time, id=f"{chat_id}_{minutes}")
        await update.message.reply_text(f"✅ {minutes} րոպե հետո կհիշեցնեմ՝ {text}")
    except Exception as e:
        await update.message.reply_text(f"Սխալ։ Օրինակ՝ /remind 10 Զանգել բժշկին")

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Դուք գրեցիք՝ {text} 😊")

async def post_init(application):
    scheduler.start()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("convert", convert_start)],
    states={
        FROM_CUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, from_cur)],
        TO_CUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, to_cur)],
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("weather", weather))
app.add_handler(CommandHandler("rate", rate))
app.add_handler(CommandHandler("remind", remind))
app.add_handler(conv_handler)
app.add_handler(MessageHandler(filters.TEXT, message))
app.run_polling()






