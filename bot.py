import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


BOT_TOKEN = os.getenv("BOT_TOKEN")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not TWELVE_DATA_API_KEY:
    raise RuntimeError("TWELVE_DATA_API_KEY is missing")


# -------------------------
# Render health server
# -------------------------

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


# -------------------------
# Market data
# -------------------------

def get_market_data(symbol="EUR/USD", interval="1min"):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": 100,
        "apikey": TWELVE_DATA_API_KEY
    }

    response = requests.get(url, params=params, timeout=15)
    data = response.json()

    if "values" not in data:
        raise RuntimeError(data.get("message", "Market data unavailable"))

    df = pd.DataFrame(data["values"])

    for column in ["open", "high", "low", "close"]:
        df[column] = pd.to_numeric(df[column])

    df = df.sort_values("datetime").reset_index(drop=True)

    return df


# -------------------------
# Indicators
# -------------------------

def calculate_indicators(df):

    close = df["close"]

    # EMA
    df["EMA9"] = close.ewm(span=9, adjust=False).mean()
    df["EMA21"] = close.ewm(span=21, adjust=False).mean()
    df["EMA50"] = close.ewm(span=50, adjust=False).mean()

    # RSI
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # Bollinger Bands
    middle = close.rolling(20).mean()
    std = close.rolling(20).std()

    df["BB_UPPER"] = middle + (2 * std)
    df["BB_LOWER"] = middle - (2 * std)

    # ATR
    high = df["high"]
    low = df["low"]

    previous_close = close.shift(1)

    tr = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs()
        ],
        axis=1
    ).max(axis=1)

    df["ATR"] = tr.rolling(14).mean()

    return df


# -------------------------
# Signal engine
# -------------------------

def generate_signal(df):

    row = df.iloc[-1]

    score = 0

    # EMA trend
    if row["EMA9"] > row["EMA21"] > row["EMA50"]:
        score += 2
    elif row["EMA9"] < row["EMA21"] < row["EMA50"]:
        score -= 2

    # RSI
    if 50 < row["RSI"] < 70:
        score += 1
    elif 30 < row["RSI"] < 50:
        score -= 1

    # MACD
    if row["MACD"] > row["MACD_SIGNAL"]:
        score += 1
    else:
        score -= 1

    # Bollinger
    if row["close"] > row["BB_LOWER"] and row["close"] < row["BB_UPPER"]:
        if row["close"] > (row["BB_UPPER"] + row["BB_LOWER"]) / 2:
            score += 1
        else:
            score -= 1

    if score >= 3:
        direction = "🟢 CALL"
    elif score <= -3:
        direction = "🔴 PUT"
    else:
        direction = "⚪ NO TRADE"

    confidence = min(95, 50 + abs(score) * 8)

    return direction, confidence, row


# -------------------------
# Telegram commands
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "Live market-data engine connected.\n\n"
        "/signal - Live EUR/USD analysis\n"
        "/help - Help\n"
        "/about - About"
    )


async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        df = get_market_data()
        df = calculate_indicators(df)

        direction, confidence, row = generate_signal(df)

        message = (
            "📊 Waseemsial AI Bot\n\n"
            "💱 EUR/USD\n"
            "⏱ 1 Minute\n\n"
            f"📌 Signal: {direction}\n"
            f"🎯 Strength: {confidence}%\n\n"
            f"RSI: {row['RSI']:.2f}\n"
            f"EMA 9: {row['EMA9']:.5f}\n"
            f"EMA 21: {row['EMA21']:.5f}\n"
            f"EMA 50: {row['EMA50']:.5f}\n"
            f"MACD: {row['MACD']:.6f}\n"
            f"ATR: {row['ATR']:.6f}\n"
            f"Price: {row['close']:.5f}\n\n"
            "⚠️ Analysis only — not guaranteed."
        )

        await update.message.reply_text(message)

    except Exception as e:

        await update.message.reply_text(
            "⚠️ Market data temporarily unavailable.\n\n"
            "Please try /signal again."
        )

        print("Signal error:", e)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "/start - Start bot\n"
        "/signal - Live signal\n"
        "/about - About bot"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 Waseemsial AI Bot\n\n"
        "Live market-data analysis\n"
        "Indicators: RSI, EMA, MACD, Bollinger Bands, ATR\n\n"
        "⚠️ No guaranteed predictions."
    )


# -------------------------
# Main
# -------------------------

def main():

    threading.Thread(
        target=run_server,
        daemon=True
    ).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))

    print("Waseemsial AI Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
