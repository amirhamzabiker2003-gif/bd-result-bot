from flask import Flask, request
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8542307257:AAF2Ni_0sVZ06jPqybogZpbFP_QOfMfMVis"

app = Flask(__name__)

users = {}

# ================= MAIN MENU =================
def main_menu():
    return ReplyKeyboardMarkup([
        ["🚀 রেজাল্ট বের করুন 🚀"],
        ["⁉️ Help & Info.", "⭐ Rate us"],
        ["📊 Statistics", "🔮 Developer Info."]
    ], resize_keyboard=True)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_chat.id] = {}
    await update.message.reply_text(
        "🎉 Welcome!\n\nResult দেখতে নিচের বাটনে চাপ দিন 👇",
        reply_markup=main_menu()
    )

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in users:
        users[chat_id] = {}

    data = users[chat_id]

    if text == "🚀 রেজাল্ট বের করুন 🚀":
        users[chat_id] = {}
        keyboard = [
            ["JSC/JDC", "SSC/Dakhil"],
            ["HSC/Alim", "DIBS"]
        ]
        await update.message.reply_text(
            "📘 Exam নির্বাচন করুন:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    if "exam" not in data:
        data["exam"] = text.split("/")[0].lower()
        keyboard = [
            ["2025","2024","2023"],
            ["2022","2021","2020"]
        ]
        await update.message.reply_text(
            "📅 Year নির্বাচন করুন:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    if "year" not in data:
        data["year"] = text
        keyboard = [
            ["Dhaka","Rajshahi","Cumilla"],
            ["Chattogram","Sylhet","Barishal"]
        ]
        await update.message.reply_text(
            "🏫 Board নির্বাচন করুন:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return

    if "board" not in data:
        data["board"] = text.lower()
        await update.message.reply_text("🆔 Roll লিখুন:")
        return

    if "roll" not in data:
        data["roll"] = text
        await update.message.reply_text("📄 Registration লিখুন:")
        return

    if "reg" not in data:
        data["reg"] = text
        session = requests.Session()
        data["session"] = session
        await send_captcha(update, data)
        return

    if text == "🔄 Reload Captcha":
        await send_captcha(update, data)
        return

    if "captcha" not in data:
        data["captcha"] = text

        payload = {
            "board": data["board"],
            "exam": data["exam"],
            "year": data["year"],
            "result_type": "1",
            "roll": data["roll"],
            "reg": data["reg"],
            "captcha": data["captcha"]
        }

        res = data["session"].post(
            "https://eboardresults.com/v2/getres",
            data=payload
        )

        result = res.json()

        if result.get("status") != 0:
            await update.message.reply_text("❌ Captcha ভুল")
            await send_captcha(update, data)
            return

        info = result["res"]
        await update.message.reply_text(f"✅ GPA: {info.get('res_detail')}")

        users[chat_id] = {}

# ================= CAPTCHA =================
async def send_captcha(update, data):
    chat_id = update.effective_chat.id

    url = "https://eboardresults.com/v2/captcha"
    r = data["session"].get(url)

    filename = f"{chat_id}.jpg"
    with open(filename,"wb") as f:
        f.write(r.content)

    await update.message.reply_photo(photo=open(filename,"rb"))
    await update.message.reply_text("🔐 Captcha লিখুন:")

# ================= TELEGRAM APP =================
telegram_app = ApplicationBuilder().token(TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# ================= FLASK ROUTES =================
@app.route("/")
def home():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    await telegram_app.process_update(update)
    return "ok"

# ================= RUN =================
if __name__ == "__main__":
    telegram_app.initialize()
    telegram_app.start()
    app.run(host="0.0.0.0", port=10000)