from flask import Flask
import threading
import telebot
import requests
import time
import re
import os

# ✅ تشغيل Web Server بسيط عشان البوت يفضل شغال
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def keep_alive():
    t = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.start()

# ✅ توكن البوت وAPI من متغيرات البيئة
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

# ✅ رسالة الترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 أهلاً بيك! ابعتلي رسالة بالشكل ده:\n`USD EGP 100`\nيعني هحول 100 دولار للجنيه.\n\nولو عايز توصلك رسالة لمرة واحدة بسعر صرف ابعتلي:\n`/alert USD EGP`",
        parse_mode='Markdown'
    )

# ✅ أمر alert لمرة واحدة
@bot.message_handler(commands=['alert'])
def handle_alert_command(message):
    try:
        parts = message.text.strip().upper().split()
        if len(parts) != 3:
            return bot.reply_to(message, "❌ الصيغة غلط. ابعتلي كده: `/alert USD EGP`", parse_mode="Markdown")

        from_curr, to_curr = parts[1], parts[2]
        chat_id = message.chat.id
        print(f"🔔 Alert requested: {chat_id} => {from_curr} to {to_curr}")
        bot.reply_to(message, f"📬 هيجيلك أول سعر لـ {from_curr} مقابل {to_curr} بعد دقيقة...")

        # ✅ تنبيه لمرة واحدة بعد دقيقة
        def send_initial_alert():
            try:
                url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/pair/{from_curr}/{to_curr}"
                data = requests.get(url, timeout=10).json()
                if data.get("result") == "success":
                    rate = round(data["conversion_rate"], 2)
                    bot.send_message(chat_id, f"📊 سعر {from_curr} مقابل {to_curr} هو: {rate}")
                else:
                    bot.send_message(chat_id, f"⚠️ مش قادر أجيب السعر لـ {from_curr}/{to_curr}")
            except Exception as e:
                print(f"❌ ERROR in send_initial_alert: {e}")

        threading.Timer(60, send_initial_alert).start()

    except Exception as e:
        print("❌ ERROR in alert command:", e)
        bot.reply_to(message, "❌ حصلت مشكلة في التنبيه، جرب تاني")

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

# ✅ تشغيل السيرفر والبوت
keep_alive()
print("🤖 Bot is running...")
bot.polling(non_stop=True, timeout=30)
