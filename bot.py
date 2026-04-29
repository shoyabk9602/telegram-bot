from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
ADMIN_ID = 7206670618
CHANNEL_ID = "@ikminvite"

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, got_link INTEGER DEFAULT 0, joined INTEGER DEFAULT 0)")
conn.commit()

# ================= DB =================
def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def set_link(uid):
    cursor.execute("UPDATE users SET got_link=1 WHERE user_id=?", (uid,))
    conn.commit()

def has_link(uid):
    cursor.execute("SELECT got_link FROM users WHERE user_id=?", (uid,))
    row = cursor.fetchone()
    return row and row[0] == 1

def set_join(uid):
    cursor.execute("UPDATE users SET joined=1 WHERE user_id=?", (uid,))
    conn.commit()

def has_join(uid):
    cursor.execute("SELECT joined FROM users WHERE user_id=?", (uid,))
    row = cursor.fetchone()
    return row and row[0] == 1

# ================= BUTTON =================
def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="join_check")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    username = f"@{user.username}" if user.username else "NoUsername"

    save_user(uid)

    # ADMIN PANEL
    if uid == ADMIN_ID:
        await update.message.reply_text("🎛️ Admin Panel Ready")
        return

    # ALREADY JOINED
    if has_join(uid):
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    # ALREADY GOT LINK
    if has_link(uid):
        await update.message.reply_text("❌ Tum already link le chuke ho\nJoin karo pehle")
        return

    # CREATE LINK
    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    set_link(uid)

    # ADMIN NOTIFICATION
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 NEW USER\n👤 {username}\n🆔 {uid}\n🔗 {link.invite_link}"
    )

    msg = await update.message.reply_text(
        f"🔥 VIP ACCESS\n\n👉 {link.invite_link}\n⏳ 60 sec",
        reply_markup=join_btn()
    )

    asyncio.create_task(countdown(msg, link.invite_link))

# ================= COUNTDOWN =================
async def countdown(msg, link):
    for i in range(60, 0, -1):
        try:
            await msg.edit_text(
                f"👉 {link}\n⏳ {i}s",
                reply_markup=join_btn()
            )
        except:
            pass
        await asyncio.sleep(1)

    await msg.edit_text("❌ Link expired\n👉 @Shoyabk96")

# ================= JOIN CHECK =================
async def join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    member = await context.bot.get_chat_member(CHANNEL_ID, uid)

    if member.status in ["member", "administrator", "creator"]:
        set_join(uid)
        await query.edit_message_text("🎉 Joined Successfully")
    else:
        await query.answer("❌ Pehle join karo", show_alert=True)

# ================= SUPPORT FORWARD =================
async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == ADMIN_ID:
        return

    text = update.message.text or update.message.caption or "Media"

    await context.bot.send_message(
        ADMIN_ID,
        f"📩 SUPPORT MSG\n\n👤 @{user.username}\n🆔 ID:{user.id}\n\n{text}"
    )

# ================= ADMIN REPLY =================
async def reply_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return

    text = update.message.reply_to_message.text

    if "ID:" in text:
        try:
            uid = int(text.split("ID:")[1].split("\n")[0])
            await context.bot.send_message(uid, f"📩 Support:\n\n{update.message.text}")
        except:
            pass

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(join_check))

# ORDER VERY IMPORTANT
app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, reply_user))
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), support_forward))

print("🔥 FINAL BOT RUNNING")
app.run_polling()
