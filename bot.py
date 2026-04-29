from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
ADMIN_ID = 7206670618
CHANNEL_ID = "@ikminvite"

# ================= DATABASE =================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS stats (date TEXT, links INTEGER, joins INTEGER)")
conn.commit()

# ================= HELPERS =================
def today():
    return datetime.now().strftime("%Y-%m-%d")

def save_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

def add_link():
    cursor.execute("SELECT links FROM stats WHERE date=?", (today(),))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE stats SET links = links + 1 WHERE date=?", (today(),))
    else:
        cursor.execute("INSERT INTO stats VALUES (?,1,0)", (today(),))
    conn.commit()

def add_join():
    cursor.execute("SELECT joins FROM stats WHERE date=?", (today(),))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE stats SET joins = joins + 1 WHERE date=?", (today(),))
    else:
        cursor.execute("INSERT INTO stats VALUES (?,0,1)", (today(),))
    conn.commit()

def get_stats():
    cursor.execute("SELECT links, joins FROM stats WHERE date=?", (today(),))
    row = cursor.fetchone()
    return row if row else (0, 0)

# ================= DATA =================
user_links = {}
joined_users = set()

def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

# ================= INVITE =================
async def send_link(update, context):
    user_id = update.effective_user.id
    save_user(user_id)

    if user_id in user_links:
        await update.message.reply_text("❌ Already got link")
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    invite_link = link.invite_link
    user_links[user_id] = invite_link
    add_link()

    msg = await update.message.reply_text(
        f"🔥 Join fast!\n👉 {invite_link}",
        reply_markup=join_button()
    )

# ================= BUTTON VERIFY =================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    if member.status in ["member", "administrator", "creator"]:
        if user_id not in joined_users:
            joined_users.add(user_id)
            add_join()

        await query.edit_message_text("🎉 Joined Successfully")
    else:
        await query.answer("❌ Join first", show_alert=True)

# ================= AUTO JOIN FIX (IMPORTANT) =================
async def track_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member

    if not chat_member:
        return

    if chat_member.chat.username != CHANNEL_ID.replace("@", ""):
        return

    user_id = chat_member.new_chat_member.user.id
    status = chat_member.new_chat_member.status

    if status in ["member", "administrator", "creator"]:
        if user_id not in joined_users:
            joined_users.add(user_id)
            add_join()

# ================= PHOTO =================
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message.reply_to_message
    caption = " ".join(context.args).replace("\\n", "\n")

    for u in get_users():
        await context.bot.send_photo(u, msg.photo[-1].file_id, caption=caption)

# ================= VIDEO =================
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message.reply_to_message
    caption = " ".join(context.args).replace("\\n", "\n")

    for u in get_users():
        await context.bot.send_video(u, msg.video.file_id, caption=caption)

# ================= AUDIO (FIXED) =================
async def audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message.reply_to_message
    caption = " ".join(context.args).replace("\\n", "\n")

    for u in get_users():
        if msg.audio:
            await context.bot.send_audio(u, msg.audio.file_id, caption=caption)
        elif msg.voice:
            await context.bot.send_voice(u, msg.voice.file_id)

# ================= STATS =================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    l, j = get_stats()
    await update.message.reply_text(f"📊 Links: {l}\n✅ Joins: {j}")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", send_link))
app.add_handler(CommandHandler("photo", photo))
app.add_handler(CommandHandler("video", video))
app.add_handler(CommandHandler("audio", audio))
app.add_handler(CommandHandler("stats", stats))

app.add_handler(CallbackQueryHandler(check_join))
app.add_handler(ChatMemberHandler(track_join, ChatMemberHandler.CHAT_MEMBER))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_link))

print("🔥 ERROR FIXED BOT RUNNING")
app.run_polling()
