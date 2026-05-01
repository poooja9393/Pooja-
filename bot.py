import os
import re
import random
import string
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Get token from Railway environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN environment variable not set!")
    exit(1)

print("=" * 50)
print("🔥 PRIME ONYX TEMP MAIL BOT 🔥")
print("=" * 50)
print("🤖 Bot is starting...")
print("📧 Token loaded from Variables")

MAILTM = "https://api.mail.tm"
sessions = {}

def random_string(length=12):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def escape_markdown(text):
    if not text:
        return ""
    # Escape special characters for Telegram
    special_chars = r'_*[]()~`>#+-=|{}.!'
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def create_account(address, password):
    try:
        resp = requests.post(f"{MAILTM}/accounts", json={"address": address, "password": password}, timeout=30)
        if resp.status_code == 201:
            return resp.json()
        return None
    except Exception as e:
        print(f"Create error: {e}")
        return None

async def get_token_mail(address, password):
    try:
        resp = requests.post(f"{MAILTM}/token", json={"address": address, "password": password}, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        print(f"Token error: {e}")
        return None

async def get_messages(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{MAILTM}/messages?page=1", headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("hydra:member", [])
        return []
    except Exception as e:
        print(f"Messages error: {e}")
        return []

async def get_message_content(token, msg_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{MAILTM}/messages/{msg_id}", headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception as e:
        print(f"Message error: {e}")
        return None

async def delete_account_mail(token, account_id):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        requests.delete(f"{MAILTM}/accounts/{account_id}", headers=headers, timeout=30)
    except Exception as e:
        print(f"Delete error: {e}")

# ============ COMMANDS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"🔥 *PRIME ONYX TEMP MAIL BOT* 🔥\n\n"
        f"👋 *Welcome, {escape_markdown(name)}!*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📧 /newmail — Generate temp email\n"
        f"📥 /inbox — Check your inbox\n"
        f"🗑 /delete — Delete email session\n"
        f"ℹ️ /myemail — Show current email\n"
        f"❓ /help — Show all commands\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🔰 *PRIME ONYX HELP* 🔰\n\n"
        f"📧 /newmail — Create new temp email\n"
        f"📥 /inbox — Check all received emails\n"
        f"🗑 /delete — Delete your email session\n"
        f"ℹ️ /myemail — Show your active email\n"
        f"📞 /support — Contact support\n\n"
        f"💡 Tip: Emails are temporary.",
        parse_mode="Markdown"
    )

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 *PRIME ONYX SUPPORT* 📞\n\n"
        f"👑 *Owner:* @Prime_X_Army",
        parse_mode="Markdown"
    )

async def newmail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id in sessions:
        await update.message.reply_text(
            f"⚠️ *You already have an active email!*\n\n"
            f"📧 `{sessions[chat_id]['email']}`\n\n"
            f"Use /delete first.",
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text("⏳ *Generating your temp email...*", parse_mode="Markdown")
    
    try:
        domain = "deltajohnsons.com"
        username = random_string(12)
        address = f"{username}@{domain}"
        password = random_string(16)
        
        account = await create_account(address, password)
        
        if not account or not account.get("id"):
            await update.message.reply_text("❌ *Failed to create email. Try again.*", parse_mode="Markdown")
            return
        
        token_data = await get_token_mail(address, password)
        
        if not token_data or not token_data.get("token"):
            await update.message.reply_text("❌ *Authentication failed. Try again.*", parse_mode="Markdown")
            return
        
        sessions[chat_id] = {
            "email": address,
            "password": password,
            "token": token_data["token"],
            "account_id": account["id"]
        }
        
        await update.message.reply_text(
            f"✅ *TEMP EMAIL READY!* ✅\n\n"
            f"📧 `{address}`\n\n"
            f"📥 Use /inbox to check emails\n"
            f"🗑 Use /delete to destroy this email",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Newmail error: {e}")
        await update.message.reply_text("❌ *Something went wrong. Try again.*", parse_mode="Markdown")

async def myemail_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in sessions:
        await update.message.reply_text("❌ *No active email. Use /newmail*", parse_mode="Markdown")
        return
    
    await update.message.reply_text(
        f"📧 *Your PRIME ONYX Temp Email:*\n\n`{sessions[chat_id]['email']}`",
        parse_mode="Markdown"
    )

async def inbox_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in sessions:
        await update.message.reply_text("❌ *No active email. Use /newmail first.*", parse_mode="Markdown")
        return
    
    await update.message.reply_text("🔄 *Checking your inbox...*", parse_mode="Markdown")
    
    try:
        messages = await get_messages(sessions[chat_id]["token"])
        
        if not messages:
            await update.message.reply_text("📭 *Your inbox is empty*", parse_mode="Markdown")
            return
        
        inbox_text = f"📬 *You have {len(messages)} email(s):*\n\n"
        for i, msg in enumerate(messages[:5]):
            inbox_text += f"*{i+1}.* From: `{msg['from']['address']}`\n    📌 {escape_markdown(msg.get('subject', 'No subject'))}\n\n"
        
        inbox_text += f"📖 *Read a message:* `/read 1`, `/read 2` etc."
        
        await update.message.reply_text(inbox_text, parse_mode="Markdown")
        sessions[chat_id]["messages"] = messages
        
    except Exception as e:
        print(f"Inbox error: {e}")
        await update.message.reply_text("❌ *Failed to fetch inbox*", parse_mode="Markdown")

async def read_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if not context.args:
        await update.message.reply_text("❌ *Usage: /read 1*", parse_mode="Markdown")
        return
    
    try:
        index = int(context.args[0]) - 1
    except:
        await update.message.reply_text("❌ *Invalid number*", parse_mode="Markdown")
        return
    
    if chat_id not in sessions or "messages" not in sessions[chat_id]:
        await update.message.reply_text("❌ *Use /inbox first*", parse_mode="Markdown")
        return
    
    if index < 0 or index >= len(sessions[chat_id]["messages"]):
        await update.message.reply_text("❌ *Invalid message number*", parse_mode="Markdown")
        return
    
    try:
        msg_id = sessions[chat_id]["messages"][index]["id"]
        full_msg = await get_message_content(sessions[chat_id]["token"], msg_id)
        
        if not full_msg:
            await update.message.reply_text("⚠️ *Could not fetch email*", parse_mode="Markdown")
            return
        
        raw_body = full_msg.get("text", "(Empty)")[:2000]
        
        # Detect OTP
        otp_match = re.search(r'\b(\d{4,8})\b', raw_body)
        otp_line = f"\n🔐 *OTP Detected:* `{otp_match.group(1)}` 👈" if otp_match else ""
        
        await update.message.reply_text(
            f"📩 *EMAIL #{index+1}*\n\n"
            f"*From:* `{full_msg['from']['address']}`\n"
            f"*Subject:* {escape_markdown(full_msg.get('subject', 'No subject'))}{otp_line}",
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(f"━━━━━━━━━━━━━━━━\n{raw_body}\n━━━━━━━━━━━━━━━━")
        
    except Exception as e:
        print(f"Read error: {e}")
        await update.message.reply_text("❌ *Failed to read message*", parse_mode="Markdown")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    if chat_id not in sessions:
        await update.message.reply_text("❌ *No active email to delete*", parse_mode="Markdown")
        return
    
    try:
        await delete_account_mail(sessions[chat_id]["token"], sessions[chat_id]["account_id"])
        del sessions[chat_id]
        await update.message.reply_text(
            f"🗑 *EMAIL DELETED!*\n\n"
            f"Your temp email has been removed.\n"
            f"Use /newmail to create a new one.",
            parse_mode="Markdown"
        )
    except Exception as e:
        if chat_id in sessions:
            del sessions[chat_id]
        await update.message.reply_text("🗑 *Session cleared*", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💡 *PRIME ONYX COMMANDS:*\n\n"
        f"/newmail — Get a temp email\n"
        f"/inbox — Check emails\n"
        f"/myemail — Show current email\n"
        f"/delete — Delete email\n"
        f"/help — All commands",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("newmail", newmail_command))
    app.add_handler(CommandHandler("myemail", myemail_command))
    app.add_handler(CommandHandler("inbox", inbox_command))
    app.add_handler(CommandHandler("read", read_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("del", delete_command))
    app.add_handler(CommandHandler("support", support_command))
    
    print("=" * 50)
    print("🔥 PRIME ONYX TEMP MAIL BOT 🔥")
    print("=" * 50)
    print("🤖 Bot Status: RUNNING")
    print("📧 Token: ✅ Loaded from Variables")
    print("🌐 Domain: deltajohnsons.com")
    print("=" * 50)
    
    app.run_polling()

if __name__ == "__main__":
    main()
