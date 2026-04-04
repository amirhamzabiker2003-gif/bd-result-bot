import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
import os

# --- FLASK SERVER ---
app_flask = Flask('')
@app_flask.route('/')
def home(): return "Result Bot is Alive!"
def run():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)
def keep_alive():
    Thread(target=run).start()

# --- BOT CONFIG ---
TOKEN = "8514395514:AAFTcY5z_-xXgVmUGFGiAw2kKiZ06cKB3T8"
users = {}

def main_menu():
    return ReplyKeyboardMarkup([["🚀 রেজাল্ট বের করুন 🚀"], ["⁉️ Help & Info.", "⭐ Rate us"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_chat.id] = {}
    await update.message.reply_text("🎉 স্বাগতম! রেজাল্ট দেখতে নিচের বাটনে চাপ দিন 👇", reply_markup=main_menu())

async def send_captcha(update, data):
    chat_id = update.effective_chat.id
    try:
        r = data["session"].get("https://eboardresults.com/v2/captcha", timeout=10)
        with open(f"{chat_id}.jpg", "wb") as f:
            f.write(r.content)
        await update.message.reply_photo(photo=open(f"{chat_id}.jpg", "rb"), caption="🔐 উপরে ছবিতে দেখা কোডটি দেখে নিচে লিখুন:")
    except:
        await update.message.reply_text("❌ ক্যাপচা লোড হচ্ছে না। আবার চেষ্টা করুন।")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    if chat_id not in users: users[chat_id] = {}
    data = users[chat_id]

    if text == "🚀 রেজাল্ট বের করুন 🚀":
        users[chat_id] = {}
        keyboard = [["JSC/JDC", "SSC/Dakhil"], ["HSC/Alim", "DIBS"]]
        await update.message.reply_text("📘 পরীক্ষার নাম নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "exam" not in data:
        data["exam"] = text.split("/")[0].lower()
        keyboard = [["2025","2024","2023"], ["2022","2021","2020"], ["2019","2018","2017"]]
        await update.message.reply_text("📅 বছর (Year) নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "year" not in data:
        data["year"] = text
        keyboard = [["Dhaka","Rajshahi","Cumilla"], ["Chattogram","Sylhet","Barishal"], ["Madrasha","Technical"]]
        await update.message.reply_text("🏫 বোর্ড নির্বাচন করুন:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return

    if "board" not in data:
        data["board"] = text.lower()
        await update.message.reply_text("🆔 রোল (Roll) নম্বর দিন:")
        return

    if "roll" not in data:
        data["roll"] = text
        await update.message.reply_text("📄 রেজিস্ট্রেশন নম্বর দিন:")
        return

    if "reg" not in data:
        data["reg"] = text
        data["session"] = requests.Session() # সেশন তৈরি
        await send_captcha(update, data)
        return

    if text == "🔄 Reload Captcha":
        await send_captcha(update, data)
        return

    if "captcha" not in data:
        payload = {
            "board": data["board"], "exam": data["exam"], "year": data["year"],
            "result_type": "1", "roll": data["roll"], "reg": data["reg"], "captcha": text
        }
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://eboardresults.com/v2/home",
            "User-Agent": "Mozilla/5.0"
        }
        try:
            res = data["session"].post("https://eboardresults.com/v2/getres", data=payload, headers=headers)
            result = res.json()
            if result.get("status") != 0:
                await update.message.reply_text("❌ ক্যাপচা ভুল! আবার ট্রাই করুন।")
                await send_captcha(update, data)
                return

            info = result["res"]
            subjects = info.get("res_data", [])
            marksheet = "\n📊 SUBJECT WISE GRADE\n━━━━━━━━━━━━━━━\n"
            for s in subjects: marksheet += f"🔹 {s.get('subject_name')}: {s.get('grade')}\n"
            
            msg = f"👨‍🎓 STUDENT INFO\n👤 Name: {info.get('name')}\n⭐ GPA: {info.get('res_detail','N/A')}\n🏫 Inst: {info.get('inst_name')}\n{marksheet}"
            await update.message.reply_text(msg, reply_markup=main_menu())
            users[chat_id] = {}
        except:
            await update.message.reply_text("❌ এরর! আবার শুরু করুন।")
            users[chat_id] = {}

if __name__ == "__main__":
    keep_alive()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()
