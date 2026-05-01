import os
import random
import string
import re
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# ✅ BAS YAHAN TOKEN DALO
BOT_TOKEN = "8361542539:AAEdao9CwKfAe15ZSpLi1EEwhoxc5EhJJPw"

BASE_URL = 'https://api.mail.tm'
users = {}
seen = {}

keyboard = ReplyKeyboardMarkup([
    ['/start', '/gen'],
    ['/inbox', '/refresh'],
    ['/otp', '/me'],
    ['/del', '/help']
], resize_keyboard=True)

def rand(n=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

def get_domain():
    r = requests.get(BASE_URL + '/domains', timeout=15)
    r.raise_for_status()
    items = r.json().get('hydra:member', [])
    return items[0]['domain'] if items else 'mail.tm'

def create_mailbox():
    domain = get_domain()
    email = f'{rand()}@{domain}'
    password = rand(12)
    requests.post(BASE_URL + '/accounts', json={'address': email, 'password': password}, timeout=15).raise_for_status()
    t = requests.post(BASE_URL + '/token', json={'address': email, 'password': password}, timeout=15)
    t.raise_for_status()
    token = t.json()['token']
    return email, password, token

def get_msgs(token):
    r = requests.get(BASE_URL + '/messages', headers={'Authorization': 'Bearer ' + token}, timeout=15)
    r.raise_for_status()
    return r.json().get('hydra:member', [])

def get_msg(token, mid):
    r = requests.get(BASE_URL + '/messages/' + mid, headers={'Authorization': 'Bearer ' + token}, timeout=15)
    r.raise_for_status()
    return r.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('📧 Temp Mail Bot Ready\nChoose an option below.', reply_markup=keyboard)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('/gen new email\n/inbox view inbox\n/refresh check now\n/otp detect OTP\n/me current email\n/del delete mailbox\n/help commands', reply_markup=keyboard)

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        email, password, token = create_mailbox()
        users[uid] = {'email': email, 'password': password, 'token': token}
        seen[uid] = set()
        await update.message.reply_text('✅ New Email Created:\n' + email, reply_markup=keyboard)
    except Exception as e:
        await update.message.reply_text('Error creating mailbox: ' + str(e))

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in users:
        await update.message.reply_text('Current Email:\n' + users[uid]['email'])
    else:
        await update.message.reply_text('No mailbox. Use /gen')

async def inbox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        await update.message.reply_text('No mailbox. Use /gen')
        return
    try:
        msgs = get_msgs(users[uid]['token'])
        if not msgs:
            await update.message.reply_text('Inbox empty.')
            return
        seen[uid] = set([m['id'] for m in msgs])
        out = []
        for m in msgs[:5]:
            d = get_msg(users[uid]['token'], m['id'])
            out.append(f"From: {d.get('from',{}).get('address','Unknown')}\nSubject: {d.get('subject','')}\nText: {(d.get('text') or '')[:500]}")
        await update.message.reply_text('\n\n----------------\n\n'.join(out))
    except Exception as e:
        await update.message.reply_text('Inbox error: ' + str(e))

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await inbox(update, context)

async def otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        await update.message.reply_text('No mailbox. Use /gen')
        return
    try:
        msgs = get_msgs(users[uid]['token'])[:5]
        codes = []
        for m in msgs:
            d = get_msg(users[uid]['token'], m['id'])
            text = (d.get('text') or '') + ' ' + str(d.get('html') or '')
            codes.extend(re.findall(r'\b\d{4,8}\b', text))
        if codes:
            await update.message.reply_text('Possible OTP Codes:\n' + '\n'.join(codes[:10]))
        else:
            await update.message.reply_text('No OTP found.')
    except Exception as e:
        await update.message.reply_text('OTP scan error: ' + str(e))

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users.pop(uid, None)
    seen.pop(uid, None)
    await update.message.reply_text('Mailbox removed from bot memory.')

async def notifier(context: ContextTypes.DEFAULT_TYPE):
    for uid, data in list(users.items()):
        try:
            msgs = get_msgs(data['token'])
            ids = set([m['id'] for m in msgs])
            old = seen.get(uid, set())
            new = ids - old
            for mid in list(new)[:3]:
                d = get_msg(data['token'], mid)
                txt = f"📩 New Email\nFrom: {d.get('from',{}).get('address','Unknown')}\nSubject: {d.get('subject','')}\n{(d.get('text') or '')[:700]}"
                await context.bot.send_message(chat_id=uid, text=txt)
            seen[uid] = ids
        except:
            pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(CommandHandler('gen', gen))
    app.add_handler(CommandHandler('me', me))
    app.add_handler(CommandHandler('inbox', inbox))
    app.add_handler(CommandHandler('refresh', refresh))
    app.add_handler(CommandHandler('otp', otp))
    app.add_handler(CommandHandler('del', delete))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.job_queue.run_repeating(notifier, interval=10, first=10)
    print('Bot running...')
    app.run_polling()

if __name__ == '__main__':
    main()