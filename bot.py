import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
import os

# --- FLASK SERVER FOR RENDER (KEEP ALIVE) ---
app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Result Bot with Marksheet is Online!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIGURATION ---
TOKEN = "8514395514:AAFTcY5z_-xXgVmUGFGiAw2kKiZ06cKB3T8" # আপনার বটের টোকেন এখানে দিন

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
        "🎉 Welcome!\n\nবিস্তারিত মার্কশিট সহ রেজাল্ট দেখতে নিচের বাটনে চাপ দিন 👇",
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
            caption="🔐 উপরে ছবিতে দেখা কোডটি (Captcha) দেখে নিচে লিখুন:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
    except Exception as e:
        await update.message.reply_text("❌ ক্যাপচা লোড করতে সমস্যা হচ্ছে। আবার চেষ্টা করুন।")

# ================= HANDLE ALL MESSAGES =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in users:
        users[chat_id] = {}

    data = users[chat_id]

    if text == "🚀 রেজাল্ট বের করুন 🚀":
        users[chat_id] = {}
        keyboard = [["JSC/JDC", "SSC/Dakhil"], ["HSC/Alim", "DIBS"]]
        await update.message.reply_text("📘 পরীক্ষার নাম (Exam) নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "exam" not in data:
        data["exam"] = text.split("/")[0].lower()
        keyboard = [["2025","2024","2023"], ["2022","2021","2020"], ["2019","2018","2017"], ["➡️ Next Page"]]
        await update.message.reply_text("📅 সাল (Year) নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "year" not in data:
        if "Next" in text:
            await update.message.reply_text("👉 পুরনো সালগুলো শীঘ্রই যুক্ত করা হবে!")
            return
        data["year"] = text
        keyboard = [["Dhaka","Rajshahi","Cumilla"], ["Chattogram","Sylhet","Barishal"], ["Dinajpur","Jashore","Mymensingh"], ["Madrasha","Technical"]]
        await update.message.reply_text("🏫 বোর্ড (Board) নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "board" not in data:
        data["board"] = text.lower()
        await update.message.reply_text("🆔 আপনার রোল (Roll) নম্বরটি লিখুন:")
        return

    if "roll" not in data:
        data["roll"] = text
        await update.message.reply_text("📄 আপনার রেজিস্ট্রেশন (Registration) নম্বর লিখুন:")
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

    # এখানে ক্যাপচা ইনপুট নিয়ে রেজাল্ট বের করা হবে
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
                await update.message.reply_text("❌ ভুল ক্যাপচা! আবার চেষ্টা করুন।")
                del data["captcha"]
                await send_captcha(update, data)
                return

            info = result["res"]
            
            # রেজাল্ট ডাটা থেকে গ্রেড লিস্ট বের করা
            subjects_list = info.get("res_data", [])
            marksheet_text = ""
            
            if subjects_list:
                marksheet_text = "\n📊 SUBJECT WISE GRADE\n━━━━━━━━━━━━━━━\n"
                for sub in subjects_list:
                    sub_name = sub.get("subject_name", "Unknown")
                    grade = sub.get("grade", "N/A")
                    marksheet_text += f"🔹 {sub_name}: {grade}\n"
            else:
                marksheet_text = "\n⚠️ Marksheet details are not available for this exam."

            gpa = info.get("res_detail","N/A").replace("GPA=","")
            sex = str(info.get("sex")).strip().lower()
            gender = "FEMALE" if sex in ["1", "f", "female"] else "MALE" if sex in ["2", "0", "m", "male"] else "UNKNOWN"

            final_msg = f"""
👨‍🎓 STUDENT INFORMATION
━━━━━━━━━━━━━━━
👤 Name: {info.get('name')}
👨 Father: {info.get('fname')}
👩 Mother: {info.get('mname')}
🚻 Gender: {gender}

📘 {data['exam'].upper()} RESULT {data['year']}
━━━━━━━━━━━━━━━
🆔 Roll: {data['roll']} | 📄 Reg: {data['reg']}
🏫 Board: {info.get('board_name')}
📊 Result: PASSED | ⭐ GPA: {gpa}
🏫 Inst: {info.get('inst_name')}

{marksheet_text}
"""
            await update.message.reply_text(final_msg, reply_markup=main_menu())
            users[chat_id] = {} # ডাটা রিসেট
            
        except Exception as e:
            await update.message.reply_text("❌ সার্ভারে সমস্যা হয়েছে। দয়া করে আবার শুরু করুন।")
            users[chat_id] = {}

# ================= RUN =================
if __name__ == "__main__":
    keep_alive() # রেন্ডারের জন্য ফ্লাস্ক সার্ভার চালু
    print("🚀 Result Bot with Marksheet is Running...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()
