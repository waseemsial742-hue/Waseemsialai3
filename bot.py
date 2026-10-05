import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Waseemsial AI Bot is running!")

    def log_message(self, format, *args):
        pass


def run_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "Welcome!\n\n"
        "📊 Trading Signal Bot\n\n"
        "Commands:\n"
        "/signal - Get signal\n"
        "/help - Help\n"
        "/about - About bot"
    )


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Waseemsial AI Bot\n\n"
        "🟢 CALL\n"
        "🔴 PUT\n"
        "⚪ NO TRADE\n\n"
        "Demo signal engine is active."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "/start - Start bot\n"
        "/signal - Get signal\n"
        "/about - About bot\n"
        "/help - Help"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "Version: 1.0\n"
        "Mode: Demo / Signal Only\n\n"
        "⚠️ Signals are not guaranteed predictions."
    )


def main():
    threading.Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))

    print("Waseemsial AI Bot is running...")
    app.run_polling()


if __name__ == "__
