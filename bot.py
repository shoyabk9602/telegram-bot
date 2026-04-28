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

BOT_TOKEN = "PASTE_YOUR_TOKEN"
ADMIN_ID = 7206670618
CHANNEL_ID = "@ikminvite"

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

# ================= DATA =================
user_links = {}
joined_users = set()

def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

# ================= COUNTDOWN =================
async def countdown(message, link):
    for i in range(60, 0, -1):
        try:
            await message.edit_text(
                f"🚀 Link:\n{link}\n\n⏳ {i} sec",
                reply_markup=join_button()
            )
        except:
            pass
        await asyncio.sleep(1)

    await message.edit_text(
        "❌ LINK EXPIRED\n👉 https://t.me/Shoyabk96"
    )

# ================= INVITE =================
async def send_link(update, context):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No username"

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

    # 🔔 ADMIN NOTIFICATION (username FIXED)
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 New User Took Link\n👤 {username}\n🆔 {user_id}"
    )

    msg = await update.message.reply_text(
        f"🚀 Link:\n{link.invite_link}",
        reply_markup=join_button()
    )

    asyncio.create_task(countdown(msg, link.invite_link))

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_link(update, context)

# ================= VERIFY =================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    if member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)

        if user_id in user_links:
            try:
                await context.bot.revoke_chat_invite_link(
                    chat_id=CHANNEL_ID,
                    invite_link=user_links[user_id]
                )
            except:
                pass

        await query.edit_message_text("🎉 Joined Successfully")
    else:
        await query.answer("❌ Join first", show_alert=True)

# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_message(u, msg)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(f"📊 Sent: {success}\n❌ Failed: {fail}")

# ================= USERS =================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"👥 Total Users: {len(get_users())}")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("users", users))

# ⚠️ IMPORTANT (commands ke baad)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_link))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 CLEAN BOT RUNNING")
app.run_polling()
