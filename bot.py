from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# CONFIG
BOT_TOKEN = "8675239901:AAHO4PJRuLMxZ_HgFzrFE3q5xP3ZMMxYBr4"
SUPPORT_BOT_TOKEN = "8742370126:AAFZpYXPlsEASY4l6lABj6kgxluAqW_t5n4"
SUPPORT_CHAT_ID = 8338253309

ADMIN_ID = 8338253309

# 🔥 PRIVATE CHANNEL ID
CHANNEL_ID = -1003685301571

SUPPORT_BOT = Bot(token=SUPPORT_BOT_TOKEN)

SUPPORT_BOT = Bot(token=SUPPORT_BOT_TOKEN)

# DATABASE
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS tickets (user_id INTEGER, messages TEXT, status TEXT)")
conn.commit()

def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

# UI
def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="join_check")]
    ])

def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🧹 Delete", callback_data="delete")]
    ])

admin_mode = {}

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    name = user.first_name

    save_user(uid)

    if uid == ADMIN_ID:
        await update.message.reply_text("Admin Panel", reply_markup=panel())
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    msg = await update.message.reply_text(
        f"<b>Hey 👋 {name}</b>\n\n👉 {link.invite_link}\n\n⏳ 60 sec",
        reply_markup=join_btn(),
        parse_mode="HTML"
    )

    asyncio.create_task(countdown(msg, link.invite_link, name))

# COUNTDOWN
async def countdown(msg, link, name):
    for i in range(60, 0, -1):
        try:
            await msg.edit_text(
                f"<b>Hey 👋 {name}</b>\n\n👉 {link}\n\n⏳ {i} sec",
                reply_markup=join_btn(),
                parse_mode="HTML"
            )
        except:
            pass
        await asyncio.sleep(1)

# JOIN
async def join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    member = await context.bot.get_chat_member(CHANNEL_ID, uid)

    if member.status in ["member", "administrator", "creator"]:
        await query.edit_message_text("Joined Successfully")
    else:
        await query.answer("Join first", show_alert=True)

# SUPPORT MERGE
async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    if uid == ADMIN_ID:
        return

    text = update.message.text or "Media"

    row = cursor.execute(
        "SELECT messages FROM tickets WHERE user_id=? AND status='open'", (uid,)
    ).fetchone()

    if row:
        new_msg = row[0] + f"\n• {text}"
        cursor.execute(
            "UPDATE tickets SET messages=? WHERE user_id=? AND status='open'",
            (new_msg, uid)
        )
    else:
        new_msg = f"• {text}"
        cursor.execute(
            "INSERT INTO tickets VALUES (?, ?, 'open')",
            (uid, new_msg)
        )

    conn.commit()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Solve", callback_data=f"solve_{uid}")]
    ])

    await SUPPORT_BOT.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text=f"📩 MERGED QUERY\n👤 {user.first_name}\n🆔 {uid}\n\n{new_msg}",
        reply_markup=kb
    )

# SOLVE
async def solve_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = int(query.data.split("_")[1])

    cursor.execute("UPDATE tickets SET status='closed' WHERE user_id=?", (uid,))
    conn.commit()

    await query.edit_message_text("✅ Solved")

# ADMIN ACTION
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    users = get_users()

    for u in users:
        try:
            await context.bot.send_message(u, update.message.text)
        except:
            pass

# RUN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(join_check, pattern="join_check"))
app.add_handler(CallbackQueryHandler(solve_ticket, pattern="solve_"))
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), support_forward))
app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), admin_action))

print("🔥 FINAL SYSTEM RUNNING")
app.run_polling()
