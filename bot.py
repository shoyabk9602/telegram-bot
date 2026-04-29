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
        [InlineKeyboardButton("🎧 Audio/Voice", callback_data="audio")],
        [InlineKeyboardButton("👥 Users", callback_data="users")]
    ])

admin_mode = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid)

    # ADMIN
    if uid == ADMIN_ID:
        await update.message.reply_text("🎛️ Panel", reply_markup=panel())
        return

    # USER INVITE
    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    await update.message.reply_text(
        f"🔥 Join karo\n👉 {link.invite_link}"
    )

# ================= PANEL CLICK =================
async def panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    mode = query.data
    admin_mode[ADMIN_ID] = mode

    if mode == "users":
        await query.message.reply_text(f"👥 {len(get_users())}")
        return

    await query.message.reply_text(f"👉 {mode.upper()} MODE ON")

# ================= ADMIN ACTION =================
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    mode = admin_mode.get(ADMIN_ID)
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
                    await context.bot.copy_message(
                        chat_id=u,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id
                    )

            success += 1
        except:
            fail += 1

    await update.message.reply_text(f"✅ {success} ❌ {fail}", reply_markup=panel())
    admin_mode[ADMIN_ID] = None

# ================= SUPPORT FORWARD =================
async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == ADMIN_ID:
        return

    text = update.message.text or update.message.caption or "Media"

    await context.bot.send_message(
        ADMIN_ID,
        f"📩 SUPPORT\n👤 @{user.username}\n🆔 ID:{user.id}\n\n{text}"
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
app.add_handler(CallbackQueryHandler(panel_click))

# 🔥 ORDER FIX (MOST IMPORTANT)
app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, reply_user))
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), support_forward))
app.add_handler(MessageHandler(filters.ALL & filters.User(ADMIN_ID), admin_action))

print("🔥 FINAL WORKING BOT")
app.run_polling()
