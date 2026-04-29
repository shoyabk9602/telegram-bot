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
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

# ================= PANEL =================
def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📸 Photo", callback_data="photo")],
        [InlineKeyboardButton("🎬 Video", callback_data="video")],
        [InlineKeyboardButton("🎧 Audio", callback_data="audio")],
        [InlineKeyboardButton("👥 Users", callback_data="users")]
    ])

user_mode = {}

# ================= JOIN BUTTON =================
def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="join_check")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id)

    # Invite system
    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    msg = await update.message.reply_text(
        f"🔥 VIP ACCESS\n👉 {link.invite_link}\n⏳ 60 sec",
        reply_markup=join_btn()
    )

    asyncio.create_task(countdown(msg, link.invite_link))

    # Admin panel
    if user.id == ADMIN_ID:
        await update.message.reply_text("🎛️ Control Panel", reply_markup=panel())

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

    await msg.edit_text("❌ Link Expired")

# ================= JOIN CHECK =================
async def join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    if member.status in ["member", "administrator", "creator"]:
        await query.edit_message_text("🎉 Joined Successfully")
    else:
        await query.answer("❌ Join first", show_alert=True)

# ================= PANEL CLICK =================
async def panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    if uid != ADMIN_ID:
        return

    mode = query.data
    user_mode[uid] = mode

    if mode == "users":
        await query.message.reply_text(f"👥 Total Users: {len(get_users())}")
        return

    await query.message.reply_text(f"👉 {mode.upper()} mode ON\nAb message/file bhejo")

# ================= HANDLE ADMIN ACTION =================
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid != ADMIN_ID:
        return

    mode = user_mode.get(uid)

    if not mode:
        return

    success, fail = 0, 0

    for u in get_users():
        try:
            if mode == "broadcast" and update.message.text:
                await context.bot.send_message(u, update.message.text)

            elif mode == "photo" and update.message.photo:
                await context.bot.send_photo(u, update.message.photo[-1].file_id)

            elif mode == "video" and update.message.video:
                await context.bot.send_video(u, update.message.video.file_id)

            elif mode == "audio":
                if update.message.audio:
                    await context.bot.send_audio(u, update.message.audio.file_id)
                elif update.message.voice:
                    await context.bot.send_voice(u, update.message.voice.file_id)

            success += 1

        except:
            fail += 1

    await update.message.reply_text(
        f"✅ Done\n📊 Sent: {success}\n❌ Failed: {fail}",
        reply_markup=panel()
    )

    user_mode[uid] = None

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

# 🔥 FIX: pattern based handlers
app.add_handler(CallbackQueryHandler(join_check, pattern="join_check"))
app.add_handler(CallbackQueryHandler(panel_click))

# 🔥 FIX: only admin messages handle
app.add_handler(MessageHandler(filters.ALL, handle_admin))

print("🔥 FINAL FIXED BOT RUNNING")
app.run_polling()
