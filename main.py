from flask import Flask
import threading
import telebot
import requests
import time

# ✅ تشغيل Web Server بسيط عشان البوت يفضل شغال
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def keep_alive():
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()

# ✅ دالة ping داخلي كل دقيقة
def auto_ping():
    while True:
        try:
            # 🔁 لينك مشروعك على Replit (مظبوط)
            ping_url = "https://38359162-e023-4446-81e2-af524afd7cd0-00-322om7ckaqs06.picard.replit.dev/"
            requests.get(ping_url)
            print("🔁 Ping sent to Replit")
        except Exception as e:
            print("⚠️ Ping failed:", e)
        time.sleep(60)

# ✅ توكن البوت
TELEGRAM_BOT_TOKEN = "7992628708:AAEfLs8QzsrHXd9HBvYyIPhe4eRVKkaqjvQ"
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ✅ API Key لموقع exchange rate
EXCHANGE_API_KEY = "1af166e77d5c99b9b9f54b2a"

# ✅ دالة لتحويل العملة
def convert_currency(from_curr, to_curr, amount):
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_curr}/{to_curr}/{amount}"
    response = requests.get(url, timeout=10)
    data = response.json()
    print("📥 API Response:", data)

    if data.get("result") == "success":
        return data["conversion_result"]
    else:
        raise ValueError(data.get("error-type", "❌ حصلت مشكلة في التحويل"))

# ✅ أمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 أهلاً بيك! ابعتلي رسالة بالشكل ده:\n`USD EGP 100`\nيعني هحول 100 دولار للجنيه.",
        parse_mode='Markdown'
    )

# ✅ التعامل مع الرسائل
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        parts = message.text.strip().upper().split()
        if len(parts) != 3:
            raise ValueError("❌ الصيغة غلط. ابعتلي كده: USD EGP 100")

        from_curr, to_curr, amount_str = parts
        amount = float(amount_str)

        result = convert_currency(from_curr, to_curr, amount)
        bot.reply_to(
            message,
            f"✅ {amount} {from_curr} = {round(result, 2)} {to_curr}"
        )

    except ValueError as ve:
        bot.reply_to(message, str(ve))
    except Exception as e:
        print("❌ UNKNOWN ERROR:", e)
        bot.reply_to(message, "❌ حصل خطأ، جرب تاني بعد شوية")

# ✅ تشغيل السيرفر + البوت + auto-ping
keep_alive()
threading.Thread(target=auto_ping).start()
print("🤖 Bot is running...")
bot.polling(non_stop=True, timeout=30)


