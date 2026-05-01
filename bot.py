import os
import random
import string
from telegram import Bot
from telegram.ext import Application, CommandHandler
from flask import Flask
import threading

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("BOT_TOKEN not set")
    exit(1)

print("Bot starting...")

sessions = {}

async def start(update, context):
    await update.message.reply_text("🔥 PRIME ONYX BOT\n\n/newmail - Create email\n/inbox - Check\n/delete - Remove")

async def newmail(update, context):
    chat_id = update.effective_chat.id
    name = ''.join(random.choices(string.ascii_lowercase, k=10))
    email = f"{name}@deltajohnsons.com"
    sessions[chat_id] = {"email": email}
    await update.message.reply_text(f"✅ Email created!\n📧 {email}")

async def myemail(update, context):
    chat_id = update.effective_chat.id
    if chat_id not in sessions:
        await update.message.reply_text("No email. Use /newmail")
        return
    await update.message.reply_text(f"📧 {sessions[chat_id]['email']}")

async def inbox(update, context):
    await update.message.reply_text("📬 Inbox:\n1. Welcome email\n2. OTP: 123456\n\nUse /read 1")

async def read(update, context):
    await update.message.reply_text("📩 Test email\nOTP: 123456")

async def delete_mail(update, context):
    chat_id = update.effective_chat.id
    if chat_id in sessions:
        del sessions[chat_id]
    await update.message.reply_text("🗑 Email deleted!")

def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newmail", newmail))
    application.add_handler(CommandHandler("myemail", myemail))
    application.add_handler(CommandHandler("inbox", inbox))
    application.add_handler(CommandHandler("read", read))
    application.add_handler(CommandHandler("delete", delete_mail))
    application.run_polling()

@app.route('/')
def home():
    return "Bot is running"

if __name__ == "__main__":
    thread = threading.Thread(target=run_bot)
    thread.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)