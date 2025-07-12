from flask import Flask
import threading
import telebot
import requests
import time
import re
import os
import schedule

# ✅ تشغيل Web Server بسيط عشان البوت يفضل شغال
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def keep_alive():
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()

# ✅ مفاتيح التوكن والـ API من البيئة
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

# ✅ أمر البدء
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 أهلاً بيك! ابعتلي:\n`USD EGP 100` علشان أحول عملة\nأو\n`/alert USD EGP` علشان توصلك رسالة يومية بالسعر الساعة 9 الصبح.\n`/stop` لإلغاء التنبيهات.",
        parse_mode='Markdown'
    )

# ✅ قائمة التنبيهات اليومية
daily_alerts = set()

# ✅ أمر alert
@bot.message_handler(commands=['alert'])
def handle_alert_command(message):
    try:
        parts = message.text.strip().upper().split()
        if len(parts) != 3:
            return bot.reply_to(message, "❌ الصيغة غلط. ابعتلي كده: `/alert USD EGP`", parse_mode="Markdown")

        from_curr, to_curr = parts[1], parts[2]
        chat_id = message.chat.id
        daily_alerts.add((chat_id, from_curr, to_curr))
        bot.reply_to(message, f"📬 هيجيلك سعر {from_curr} مقابل {to_curr} كل يوم الساعة 9 صباحًا")
        print(f"✅ Daily alert added: {chat_id} => {from_curr} to {to_curr}")
    except Exception as e:
        print("❌ ERROR in /alert:", e)
        bot.reply_to(message, "❌ حصلت مشكلة في التنبيه، جرب تاني")

# ✅ أمر /stop
@bot.message_handler(commands=['stop'])
def handle_stop(message):
    chat_id = message.chat.id
    before = len(daily_alerts)
    daily_alerts.difference_update({item for item in daily_alerts if item[0] == chat_id})
    after = len(daily_alerts)
    if before != after:
        bot.reply_to(message, "🛑 تم إلغاء كل التنبيهات اليومية ليك")
    else:
        bot.reply_to(message, "❌ مفيش تنبيهات مفعّلة ليك")

# ✅ إرسال التنبيهات اليومية الساعة 9:00
def send_daily_alerts():
    print("🔁 Running daily alerts...")
    for chat_id, from_curr, to_curr in daily_alerts:
        try:
            url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_curr}/{to_curr}"
            data = requests.get(url, timeout=10).json()
            if data.get("result") == "success":
                rate = round(data["conversion_rate"], 2)
                bot.send_message(chat_id, f"📊 السعر اليوم: {from_curr} مقابل {to_curr} = {rate}")
            else:
                bot.send_message(chat_id, f"⚠️ مش قادر أجيب السعر لـ {from_curr}/{to_curr}")
        except Exception as e:
            print(f"❌ ERROR sending alert to {chat_id}: {e}")

# ✅ جدولة الساعة 9 صباحًا
schedule.every().day.at("09:00").do(send_daily_alerts)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# ✅ التعامل مع رسائل التحويل
@bot.message_handler(func=lambda m: re.match(r'^[A-Z]{3} [A-Z]{3} \d+(\.\d+)?$', m.text.strip().upper()))
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

# ✅ تشغيل البوت والسيرفر والجدولة
keep_alive()
threading.Thread(target=run_scheduler).start()
print("🤖 Bot is running...")
bot.polling(non_stop=True, timeout=30)
