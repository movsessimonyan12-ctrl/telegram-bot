from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8702251463:AAE5ql6GTpraeABYYy5Bv0tt3zEvOUjUPoU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Բարև! Ես բոտ եմ 🤖\nՕգտագործիր /help հրամանը։")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Հրամաններ:\n/start - Սկսել\n/help - Օգնություն\n/about - Բոտի մասին")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ես Python-ով գրված Telegram բոտ եմ 🐍")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.run_polling()
