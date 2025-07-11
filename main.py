import telebot
import requests
import os

# ✅ جلب المفاتيح من environment variables
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

# ✅ تشغيل البوت
print("🤖 Bot is running...")
bot.polling(non_stop=True, timeout=30)


