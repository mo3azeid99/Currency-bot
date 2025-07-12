from flask import Flask
import threading
import telebot
import requests
import schedule
import time
import re
import os

# ✅ Web Server بسيط علشان Railway يفضل مشغل البوت
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def keep_alive():
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()

# ✅ متغيرات البيئة
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# ✅ دالة تحويل العملات
def convert_currency(from_curr, to_curr, amount):
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_curr}/{to_curr}/{amount}"
    response = requests.get(url, timeout=10)
    data = response.json()
    print("📥 API Response:", data)

    if data.get("result") == "success":
        return data["conversion_result"]
    else:
        raise ValueError(data.get("error-type", "❌ حصلت مشكلة في التحويل"))

# ✅ رسالة البداية
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 أهلاً بيك!\n\nابعتلي رسالة بالشكل ده:\n`USD EGP 100`\nعشان أحوللك العملة.\n\nولو عايز توصلك رسالة يومية بسعر صرف عملة ابعتلي:\n`alert USD TO EGP`\nوللإلغاء ابعت `/stop`",
        parse_mode='Markdown'
    )

# ✅ رسائل التحويل
@bot.message_handler(func=lambda m: re.match(r'^[A-Z]{3} [A-Z]{3} \d+(\.\d+)?$', m.text.strip().upper()))
def handle_conversion(message):
    try:
        parts = message.text.strip().upper().split()
        from_curr, to_curr, amount_str = parts
        amount = float(amount_str)
        result = convert_currency(from_curr, to_curr, amount)
        bot.reply_to(message, f"✅ {amount} {from_curr} = {round(result, 2)} {to_curr}")
    except Exception as e:
        print("❌ Error:", e)
        bot.reply_to(message, "❌ حصل خطأ، جرب تاني بعد شوية")

# ✅ تخزين التنبيهات اليومية
daily_alerts = set()

# ✅ أمر alert
@bot.message_handler(func=lambda m: re.match(r'^alert\s+[A-Z]{3}\s+TO\s+[A-Z]{3}$', m.text.strip().upper()))
def handle_alert(message):
    match = re.match(r'^alert\s+([A-Z]{3})\s+TO\s+([A-Z]{3})$', message.text.strip().upper())
    if match:
        from_curr, to_curr = match.groups()
        chat_id = message.chat.id
        daily_alerts.add((chat_id, from_curr, to_curr))
        bot.reply_to(message, f"📬 هنبعتلك كل يوم سعر {from_curr} مقابل {to_curr}")

# ✅ أمر /stop لإلغاء التنبيهات
@bot.message_handler(commands=['stop'])
def handle_stop(message):
    chat_id = message.chat.id
    removed = len([item for item in daily_alerts if item[0] == chat_id])
    daily_alerts.difference_update({item for item in daily_alerts if item[0] == chat_id})
    if removed:
        bot.reply_to(message, "🛑 تم إلغاء كل التنبيهات اليومية")
    else:
        bot.reply_to(message, "❌ مفيش تنبيهات مفعّلة ليك")

# ✅ إرسال سعر الصرف يوميًا
def send_daily_alerts():
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
            print(f"❌ Error: {e}")

# ✅ جدولة الإرسال يوميًا الساعة 09:00 صباحًا
schedule.every().day.at("09:00").do(send_daily_alerts)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# ✅ fallback لأي رسالة غير مفهومة
@bot.message_handler(func=lambda m: True)
def handle_unknown(message):
    bot.reply_to(
        message,
        "❌ مش فاهم الرسالة.\nلو عايز تحول عملة ابعت: `USD EGP 100`\nلو عايز تنبيه يومي ابعت: `alert USD TO EGP`\n\nوللإلغاء: `/stop`",
        parse_mode="Markdown"
    )

# ✅ تشغيل السيرفر والبوت والجدولة
keep_alive()
threading.Thread(target=run_scheduler).start()
print("🤖 Bot is running...")
bot.polling(non_stop=True, timeout=30)

