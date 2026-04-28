from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
ADMIN_ID = 7206670618

# ================= DATABASE =================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

def save_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text("👋 Welcome!")

async def auto_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)

# ================= TEXT BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    users = get_users()

    success, fail = 0, 0

    for u in users:
        try:
            await context.bot.send_message(u, msg)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(
        f"📊 Report:\n✅ Sent: {success}\n❌ Failed: {fail}"
    )

# ================= PHOTO =================
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Photo pe reply karo")
        return

    file_id = update.message.reply_to_message.photo[-1].file_id
    caption = " ".join(context.args)

    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_photo(u, file_id, caption=caption)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(
        f"📸 Photo Report:\n✅ {success}\n❌ {fail}"
    )

# ================= BUTTON =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Use: /button msg link")
        return

    msg = context.args[0]
    link = context.args[1]

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👉 Open", url=link)]
    ])

    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_message(u, msg, reply_markup=kb)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(
        f"🔘 Button Report:\n✅ {success}\n❌ {fail}"
    )

# ================= SCHEDULE =================
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        delay = int(context.args[0])
        msg = " ".join(context.args[1:])
    except:
        await update.message.reply_text("Use: /schedule seconds msg")
        return

    await update.message.reply_text(f"⏳ Scheduled in {delay}s")

    await asyncio.sleep(delay)

    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_message(u, msg)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(
        f"⏰ Scheduled Done\n✅ {success}\n❌ {fail}"
    )

# ================= USERS =================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"👥 Users: {len(get_users())}")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("photo", photo))
app.add_handler(CommandHandler("button", button))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(CommandHandler("users", users))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_save))

print("🔥 ALL FEATURES RUNNING")
app.run_polling()
