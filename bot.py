import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "Welcome!\n\n"
        "📊 Trading Signal Bot\n\n"
        "/signal - Get signal\n"
        "/help - Help\n"
        "/about - About bot"
    )


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Waseemsial AI Bot\n\n"
        "🟢 CALL / 🔴 PUT / ⚪ NO TRADE\n\n"
        "Demo signal engine is active."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "/start - Start bot\n"
        "/signal - Get signal\n"
        "/about - About bot"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "Version: 1.0\n"
        "Mode: Demo / Signal Only"
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))

    print("Waseemsial AI Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
