import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
import os

# --- FLASK SERVER FOR RENDER ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Second Bot is Alive!"

def run():
    # Render এর PORT এনভায়রনমেন্ট ভেরিয়েবল ব্যবহার করা
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- ORIGINAL BOT CODE ---
TOKEN = "YOUR_BOT_TOKEN" # আপনার টোকেনটি এখানে দিন

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

# ================= CAPTCHA FUNCTION =================
async def send_captcha(update, data):
    chat_id = update.effective_chat.id
    url = "https://eboardresults.com/v2/captcha"
    
    try:
        r = data["session"].get(url)
        file_path = f"{chat_id}.jpg"
        with open(file_path, "wb") as f:
            f.write(r.content)

        keyboard = [["🔄 Reload Captcha"]]
        await update.message.reply_photo(
            photo=open(file_path, "rb"),
            caption="🔐 উপরে ছবিতে দেখা কোডটি (Captcha) লিখুন:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        # ফাইলটি পাঠানোর পর ডিলিট করে দেওয়া ভালো (অপশনাল)
    except Exception as e:
        await update.message.reply_text("❌ ক্যাপচা লোড করতে সমস্যা হচ্ছে। আবার চেষ্টা করুন।")

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in users:
        users[chat_id] = {}

    data = users[chat_id]

    if text == "🚀 রেজাল্ট বের করুন 🚀":
        users[chat_id] = {}
        keyboard = [["JSC/JDC", "SSC/Dakhil"], ["HSC/Alim", "DIBS"]]
        await update.message.reply_text("📘 Exam নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "exam" not in data:
        data["exam"] = text.split("/")[0].lower()
        keyboard = [["2025","2024","2023"], ["2022","2021","2020"], ["2019","2018","2017"], ["➡️ Next Page"]]
        await update.message.reply_text("📅 Year নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "year" not in data:
        if "Next" in text:
            await update.message.reply_text("👉 Older year selection is coming soon!")
            return
        data["year"] = text
        keyboard = [["Dhaka","Rajshahi","Cumilla"], ["Chattogram","Sylhet","Barishal"], ["Dinajpur","Jashore","Mymensingh"], ["Madrasha","Technical"]]
        await update.message.reply_text("🏫 Board নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
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
        if "session" in data:
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
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://eboardresults.com",
            "Referer": "https://eboardresults.com/v2/home",
            "User-Agent": "Mozilla/5.0"
        }

        try:
            res = data["session"].post("https://eboardresults.com/v2/getres", data=payload, headers=headers)
            result = res.json()

            if result.get("status") != 0:
                await update.message.reply_text("❌ Captcha ভুল অথবা সার্ভার এরর! আবার চেষ্টা করো।")
                del data["captcha"] # ভুল ক্যাপচা হলে ডাটা থেকে মুছে ফেলা যাতে আবার ইনপুট নেওয়া যায়
                await send_captcha(update, data)
                return

            info = result["res"]
            gpa = info.get("res_detail","N/A").replace("GPA=","")
            
            # Gender Fix
            sex = str(info.get("sex")).strip().lower()
            gender = "FEMALE" if sex in ["1", "f", "female"] else "MALE" if sex in ["2", "0", "m", "male"] else "UNKNOWN"

            msg = f"""
👨‍🎓 STUDENT INFORMATION
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
📊 Result: PASSED
⭐ GPA: {gpa}
🏫 Institute: {info.get('inst_name')}
"""
            await update.message.reply_text(msg, reply_markup=main_menu())
            users[chat_id] = {}
        except Exception as e:
            await update.message.reply_text("❌ রেজাল্ট আনতে সমস্যা হয়েছে। আবার শুরু করুন।")
            users[chat_id] = {}

# ================= RUN =================
if __name__ == "__main__":
    # ১. প্রথমে ফ্লাস্ক চালু হবে
    keep_alive()
    
    # ২. এরপর টেলিগ্রাম বট চালু হবে
    print("🚀 SECOND BOT STARTED SUCCESSFULLY ✅")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()
