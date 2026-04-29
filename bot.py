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
    ContextTypes,
    filters
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
        cursor.execute("UPDATE stats SET links=links+1 WHERE date=?", (today(),))
    else:
        cursor.execute("INSERT INTO stats VALUES (?,1,0)", (today(),))
    conn.commit()

def add_join():
    cursor.execute("SELECT joins FROM stats WHERE date=?", (today(),))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE stats SET joins=joins+1 WHERE date=?", (today(),))
    else:
        cursor.execute("INSERT INTO stats VALUES (?,0,1)", (today(),))
    conn.commit()

def get_stats():
    cursor.execute("SELECT links, joins FROM stats WHERE date=?", (today(),))
    row = cursor.fetchone()
    return row if row else (0, 0)

# ================= GLOBAL =================
user_links = {}
joined_users = set()

def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="join_check")]
    ])

# ================= INVITE =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username

    save_user(user_id)

    if user_id in user_links:
        await update.message.reply_text("❌ Tum already link le chuke ho")
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    user_links[user_id] = link.invite_link
    add_link()

    links, joins = get_stats()

    # admin notification
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 NEW LINK\nUser: @{username}\nID: {user_id}\n\n{link.invite_link}\n\nLinks:{links} Joins:{joins}"
    )

    msg = await update.message.reply_text(
        f"🔥 LIMITED ACCESS\n\n👉 {link.invite_link}\n⏳ 60 sec only",
        reply_markup=join_btn()
    )

    asyncio.create_task(countdown(msg, link.invite_link))

# ================= COUNTDOWN =================
async def countdown(msg, link):
    for i in range(60, 0, -1):
        try:
            await msg.edit_text(
                f"🔥 LINK\n\n{link}\n⏳ {i}s",
                reply_markup=join_btn()
            )
        except:
            pass
        await asyncio.sleep(1)

    await msg.edit_text("❌ LINK EXPIRED\n👉 @Shoyabk96")

# ================= JOIN BUTTON =================
async def join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    if member.status in ["member", "administrator", "creator"]:
        if user_id not in joined_users:
            joined_users.add(user_id)
            add_join()
        await query.edit_message_text("🎉 Joined Successfully")
    else:
        await query.answer("❌ Pehle join karo", show_alert=True)

# ================= AUTO JOIN =================
async def auto_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.chat_member.chat
    if chat.username != CHANNEL_ID.replace("@", ""):
        return

    user_id = update.chat_member.new_chat_member.user.id
    status = update.chat_member.new_chat_member.status

    if status in ["member", "administrator", "creator"]:
        if user_id not in joined_users:
            joined_users.add(user_id)
            add_join()

# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args).replace("\\n", "\n")

    for u in get_users():
        try:
            await context.bot.send_message(u, msg)
        except:
            pass

    await update.message.reply_text("✅ Broadcast done")

# ================= PHOTO =================
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message.reply_to_message
    caption = " ".join(context.args).replace("\\n", "\n")

    for u in get_users():
        await context.bot.send_photo(u, msg.photo[-1].file_id, caption=caption)

    await update.message.reply_text("📸 Done")

# ================= VIDEO =================
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = update.message.reply_to_message
    caption = " ".join(context.args).replace("\\n", "\n")

    for u in get_users():
        await context.bot.send_video(u, msg.video.file_id, caption=caption)

    await update.message.reply_text("🎬 Done")

# ================= AUDIO =================
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

    await update.message.reply_text("🎧 Done")

# ================= USERS =================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"👥 Users: {len(get_users())}")

# ================= STATS =================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    l, j = get_stats()
    await update.message.reply_text(f"📊 Links: {l}\nJoins: {j}")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("photo", photo))
app.add_handler(CommandHandler("video", video))
app.add_handler(CommandHandler("audio", audio))
app.add_handler(CommandHandler("users", users))
app.add_handler(CommandHandler("stats", stats))

app.add_handler(CallbackQueryHandler(join_check))
app.add_handler(ChatMemberHandler(auto_join, ChatMemberHandler.CHAT_MEMBER))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

print("🔥 BOT RUNNING PERFECTLY")
app.run_polling()
