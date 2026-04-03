from flask import Flask, request
import requests
import asyncio

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8773704187:AAGTsdTedZNUuBYaKsrNUHE1DLt7sjakHJg"

app = Flask(__name__)
application = ApplicationBuilder().token(TOKEN).build()

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

    # MAIN BUTTON
    if text == "🚀 রেজাল্ট বের করুন 🚀":
        users[chat_id] = {}
        keyboard = [["JSC/JDC","SSC/Dakhil"],["HSC/Alim","DIBS"]]
        await update.message.reply_text("📘 Exam নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    # EXAM
    if "exam" not in data:
        data["exam"] = text.split("/")[0].lower()
        keyboard = [["2025","2024","2023"],["2022","2021","2020"],["2019","2018","2017"]]
        await update.message.reply_text("📅 Year নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    # YEAR
    if "year" not in data:
        data["year"] = text
        keyboard = [["Dhaka","Rajshahi","Cumilla"],["Chattogram","Sylhet","Barishal"],["Dinajpur","Jashore","Mymensingh"],["Madrasha","Technical"]]
        await update.message.reply_text("🏫 Board নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    # BOARD
    if "board" not in data:
        data["board"] = text.lower()
        await update.message.reply_text("🆔 Roll লিখুন:")
        return

    # ROLL
    if "roll" not in data:
        data["roll"] = text
        await update.message.reply_text("📄 Registration লিখুন:")
        return

    # REG
    if "reg" not in data:
        data["reg"] = text
        data["session"] = requests.Session()
        await send_captcha(update, data)
        return

    # CAPTCHA RELOAD
    if text == "🔄 Reload Captcha":
        await send_captcha(update, data)
        return

    # CAPTCHA SUBMIT
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

        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://eboardresults.com",
            "Referer": "https://eboardresults.com/v2/home",
            "User-Agent": "Mozilla/5.0"
        }

        res = data["session"].post(
            "https://eboardresults.com/v2/getres",
            data=payload,
            headers=headers
        )

        result = res.json()

        if result.get("status") != 0:
            await update.message.reply_text("❌ Captcha ভুল, আবার চেষ্টা করো")
            await send_captcha(update, data)
            return

        info = result["res"]
        gpa = info.get("res_detail","N/A").replace("GPA=","")

        sex = str(info.get("sex")).strip().lower()
        if sex in ["1","f","female"]:
            gender = "FEMALE"
        elif sex in ["2","0","m","male"]:
            gender = "MALE"
        else:
            gender = "UNKNOWN"

        msg = f"""👨‍🎓 STUDENT INFORMATION
━━━━━━━━━━━━━━━
👤 Name: {info.get('name')}
👨 Father: {info.get('fname')}
👩 Mother: {info.get('mname')}
📅 DOB: {info.get('dob')}
🚻 Gender: {gender}

📘 {data['exam'].upper()} RESULT {data['year']}
━━━━━━━━━━━━━━━
🆔 Roll: {data['roll']}
📄 Reg: {data['reg']}

🏫 Board: {info.get('board_name')}
📚 Group: {info.get('stud_group')}

📊 Result: PASSED
⭐ GPA: {gpa}

🏫 Institute: {info.get('inst_name')}
"""

        await update.message.reply_text(msg, reply_markup=main_menu())
        users[chat_id] = {}

# ================= CAPTCHA =================
async def send_captcha(update, data):
    chat_id = update.effective_chat.id
    r = data["session"].get("https://eboardresults.com/v2/captcha")

    filename = f"{chat_id}.jpg"
    with open(filename, "wb") as f:
        f.write(r.content)

    keyboard = [["🔄 Reload Captcha"]]

    await update.message.reply_photo(
        photo=open(filename, "rb"),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    await update.message.reply_text("🔐 Captcha লিখুন:")

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "ok"

@app.route("/")
def home():
    return "Bot is running!"

# ================= HANDLERS =================
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

# ================= RUN (LOCAL TEST) =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
