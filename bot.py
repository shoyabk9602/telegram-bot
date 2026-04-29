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
        [InlineKeyboardButton("🎧 Audio/Voice", callback_data="audio")],
        [InlineKeyboardButton("👥 Users", callback_data="users")]
    ])

user_mode = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text("🎛️ Control Panel", reply_markup=panel())

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

# ================= HANDLE ADMIN =================
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        return

    mode = user_mode.get(uid)
    if not mode:
        return

    caption = update.message.caption or update.message.text or ""
    caption = caption.replace("\\n", "\n")

    success, fail = 0, 0

    for u in get_users():
        try:
            if mode == "broadcast" and update.message.text:
                await context.bot.send_message(u, caption)

            elif mode == "photo" and update.message.photo:
                await context.bot.send_photo(
                    u,
                    update.message.photo[-1].file_id,
                    caption=caption
                )

            elif mode == "video" and update.message.video:
                await context.bot.send_video(
                    u,
                    update.message.video.file_id,
                    caption=caption
                )

            elif mode == "audio":
                msg = update.message

                # 🔥 AUDIO
                if msg.audio:
                    await context.bot.send_audio(u, msg.audio.file_id, caption=caption)

                # 🔥 VOICE FIX (IMPORTANT)
                elif msg.voice:
                    await context.bot.copy_message(
                        chat_id=u,
                        from_chat_id=update.effective_chat.id,
                        message_id=msg.message_id
                    )

            success += 1

        except Exception as e:
            fail += 1

    await update.message.reply_text(
        f"✅ Done\n📊 Sent: {success}\n❌ Failed: {fail}",
        reply_markup=panel()
    )

    user_mode[uid] = None

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(panel_click))
app.add_handler(MessageHandler(filters.ALL, handle_admin))

print("🔥 VOICE FIX BOT RUNNING")
app.run_polling()
