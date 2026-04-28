from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
CHANNEL_ID = "@ikminvite"
ADMIN_ID = 7206670618

# DATABASE
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

def save_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# DATA
user_links = {}
joined_users = set()

def join_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("✅ I Joined", callback_data="check_join")]])

# COUNTDOWN
async def countdown_timer(message, invite_link, seconds):
    for i in range(seconds, 0, -1):
        try:
            await message.edit_text(
                f"👉 {invite_link}\n⏳ {i} sec",
                reply_markup=join_button()
            )
        except:
            pass
        await asyncio.sleep(1)

    await message.edit_text(
        "❌ LINK EXPIRED\n👉 https://t.me/Shoyabk96"
    )

# INVITE
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)

    if user_id in joined_users:
        await update.message.reply_text("✅ Already joined")
        return

    if user_id in user_links:
        await update.message.reply_text("❌ Already got link")
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    user_links[user_id] = link.invite_link

    msg = await update.message.reply_text(link.invite_link, reply_markup=join_button())
    asyncio.create_task(countdown_timer(msg, link.invite_link, 60))

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await auto_reply(update, context)

# VERIFY
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    if member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)
        await update.callback_query.edit_message_text("🎉 Joined")

# BROADCAST
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    for user in get_users():
        try:
            await context.bot.send_message(user, msg)
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text("✅ Broadcast Done")

# PHOTO
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Photo pe reply karo")
        return

    file_id = update.message.reply_to_message.photo[-1].file_id
    caption = " ".join(context.args)

    for user in get_users():
        try:
            await context.bot.send_photo(user, file_id, caption=caption)
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text("📸 Done")

# USERS (🔥 FIX)
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    total = len(get_users())
    await update.message.reply_text(f"👥 Total Users: {total}")

# RUN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("photo", photo))
app.add_handler(CommandHandler("users", users))  # 🔥 IMPORTANT
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 RUNNING...")
app.run_polling()
