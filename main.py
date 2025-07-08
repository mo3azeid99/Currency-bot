from keep_alive import keep_alive
import telebot
import requests
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def convert_currency(from_curr, to_curr, amount):
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_curr}/{to_curr}/{amount}"
    res = requests.get(url, timeout=10).json()
    if res.get("result") == "success":
        return res["conversion_result"]
    else:
        raise ValueError(res.get("error-type", "❌ حصلت مشكلة في التحويل"))

@bot.message_handler(commands=['start'])
def send_welcome(m):
    bot.reply_to(m, "👋 ابعتلي كده: `USD EGP 100`")

@bot.message_handler(func=lambda m: True)
def handle_message(m):
    try:
        parts = m.text.strip().upper().split()
        if len(parts) != 3:
            raise ValueError("❌ الصيغة غلط. ابعتلي: USD EGP 100")
        from_curr, to_curr, amt = parts
        amt = float(amt)
        res = convert_currency(from_curr, to_curr, amt)
        bot.reply_to(m, f"✅ {amt} {from_curr} = {round(res, 2)} {to_curr}")
    except Exception as e:
        bot.reply_to(m, str(e))

keep_alive()
bot.polling(non_stop=True, timeout=30)
