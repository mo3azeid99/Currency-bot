from flask import Flask
import threading
import telebot
import requests
import schedule
import time
import re
import os

# ✅ تشغيل Web Server بسيط علشان البوت يفضل شغال
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def keep_alive():
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()

# ✅ المتغيرات السرية من Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

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
        "👋 أهلاً بيك! ابعتلي رسالة بالشكل ده:\n`USD EGP 100`\nيعني هحول 100 دولار للجنيه.\n\nولو عايز توصلك رسالة يومية بسعر صرف عملة ابعتلي:\n`/alert USD EGP`\nوللإلغاء ابعت `/stop`",
        parse_mode='Markdown'
    )

# ✅ تخزين التنبيهات اليومية
daily_alerts = set()

# ✅ أمر /alert USD EGP
@bot.message_handler(commands=['alert'])
def handle_alert_command(message):
    try:
        parts = message.text.strip().upper().split()
        if len(parts) != 3:
            raise ValueError("❌ الصيغة غلط. ابعتلي كده: /alert USD EGP")

        _, from_curr, to_curr = parts
        chat_id = message.chat.id
        daily_alerts.add((chat_id, from_curr, to_curr))
        print(f"🔔 Alert added: {chat_id} - {from_curr}/{to_curr}")
        bot.reply_to(message, f"📬 هيوصلك سعر {from_curr} مقابل {to_curr} كل يوم الساعة 9 صباحًا")

    except Exception as e:
        print("❌ ALERT ERROR:", e)
        bot.reply_to(message, "❌ الصيغة غلط. ابعتلي كده: /alert USD EGP")

# ✅ أمر /stop لإلغاء كل التنبيهات
@bot.message_handler(commands=['stop'])
def handle_stop(message):
    chat_id = message.chat.id
    before = len(daily_alerts)
    daily_alerts.difference_update({item for item in daily_alerts if item[0] == chat_id})
    after = len(daily_alerts)
    print(f"🛑 Removed {before - after} alerts for chat_id: {chat_id}")
    if before != after:
        bot.reply_to(message, "🛑 تم إلغاء كل التنبيهات اليومية")
    else:
        bot.reply_to(message, "❌ مفيش تنبيهات مفعّلة ليك")

# ✅ التعامل مع رسائل التحويل العادية (غير الأوامر)
@bot.message_handler(func=lambda m: not m.text.startswith("/") and re.match(r'^[A-Z]{3} [A-Z]{3} \d+(\.\d+)?$', m.text.strip().upper()))
def handle_conversion(message):
    try:
        parts = message.text.strip().upper().split()
        from_curr, to_curr, amount_str = parts
        amount = float(amount_str)

        result = convert_currency(from_curr, to_curr, amount)
        bot.reply_to(message, f"✅ {amount} {from_curr} = {round(result, 2)} {to_curr}")
    except ValueError as ve:
        bot.reply_to(message, str(ve))
    except Exception as e:
        print("❌ UNKNOWN ERROR:", e)
        bot.reply_to(message, "❌ حصل خطأ، جرب تاني بعد شوية")

# ✅ دالة إرسال سعر الصرف للمستخدمين يوميًا
def send_daily_alerts():
    print("⏰ Running scheduled alerts...")
    for chat_id, from_curr, to_curr in daily_alerts:
        try:
            url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_curr}/{to_curr}"
            data = requests.get(url, timeout=10).json()
            if data.get("result") == "success":
                rate = round(data["conversion_rate"], 2)
                bot.send_message(chat_id, f"📊 سعر {from_curr} مقابل {to_curr} هو: {rate}")
            else:
                bot.send_message(chat_id, f"⚠️ مش قادر أجيب السعر لـ {from_curr}/{to_curr}")
        except Exception as e:
            print(f"❌ ERROR: {e}")

# ✅ جدولة المهمة يوميًا الساعة 9 صباحًا
schedule.every().day.at("09:00").do(send_daily_alerts)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# ✅ تشغيل السيرفر والبوت والجدولة
keep_alive()
threading.Thread(target=run_scheduler).start()
print("🤖 Bot is running...")
bot.polling(non_stop=True, timeout=30)

