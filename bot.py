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
CHANNEL_ID = "@ikminvite"  # public channel

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS msgs (user_id INTEGER, msg_id INTEGER)")
conn.commit()

def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

def save_msg(uid, mid):
    cursor.execute("INSERT INTO msgs VALUES (?,?)", (uid, mid))
    conn.commit()

def get_msgs():
    cursor.execute("SELECT user_id, msg_id FROM msgs")
    return cursor.fetchall()

def clear_msgs():
    cursor.execute("DELETE FROM msgs")
    conn.commit()

# ================= UI =================
def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📸 Photo", callback_data="photo")],
        [InlineKeyboardButton("🎬 Video", callback_data="video")],
        [InlineKeyboardButton("🎧 Audio/Voice", callback_data="audio")],
        [InlineKeyboardButton("🧹 Delete", callback_data="delete")],
        [InlineKeyboardButton("👥 Users", callback_data="users")]
    ])

user_mode = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid)

    if uid == ADMIN_ID:
        await update.message.reply_text("🎛️ Control Panel", reply_markup=panel())
    else:
        await update.message.reply_text(
            "👋 Welcome!\nKoi problem ho to yahin msg karo, support mil jayega."
        )

# ================= PANEL =================
async def panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    mode = query.data
    user_mode[ADMIN_ID] = mode

    if mode == "users":
        await query.message.reply_text(f"👥 Users: {len(get_users())}")
        return

    await query.message.reply_text(f"👉 {mode.upper()} mode ON\nAb bhejo")

# ================= ADMIN ACTION =================
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        return

    mode = user_mode.get(uid)
    if not mode:
        return

    success, fail = 0, 0

    # DELETE
    if mode == "delete":
        for u, mid in get_msgs():
            try:
                await context.bot.delete_message(u, mid)
                success += 1
            except:
                fail += 1
        clear_msgs()
        await update.message.reply_text(f"🧹 Deleted {success}")
        user_mode[uid] = None
        return

    # SEND
    for u in get_users():
        try:
            if mode == "broadcast" and update.message.text:
                msg = await context.bot.send_message(u, update.message.text)

            elif mode == "photo" and update.message.photo:
                msg = await context.bot.send_photo(u, update.message.photo[-1].file_id, caption=update.message.caption)

            elif mode == "video" and update.message.video:
                msg = await context.bot.send_video(u, update.message.video.file_id, caption=update.message.caption)

            elif mode == "audio":
                if update.message.audio:
                    msg = await context.bot.send_audio(u, update.message.audio.file_id, caption=update.message.caption)
                elif update.message.voice:
                    msg = await context.bot.copy_message(
                        chat_id=u,
                        from_chat_id=update.effective_chat.id,
                        message_id=update.message.message_id
                    )

            save_msg(u, msg.message_id)
            success += 1

        except:
            fail += 1

    await update.message.reply_text(f"✅ Sent: {success} ❌ {fail}", reply_markup=panel())
    user_mode[uid] = None

# ================= SUPPORT FORWARD =================
async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == ADMIN_ID:
        return

    msg = update.message
    text = msg.text or msg.caption or "Media"

    await context.bot.send_message(
        ADMIN_ID,
        f"📩 SUPPORT MSG\n\n"
        f"👤 @{user.username}\n"
        f"🆔 ID:{user.id}\n\n"
        f"{text}"
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

            await context.bot.send_message(
                uid,
                f"📩 Support Reply:\n\n{update.message.text}"
            )
        except:
            pass

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(panel_click))

# 🔥 ORDER IMPORTANT
app.add_handler(MessageHandler(filters.TEXT & filters.REPLY, reply_user))
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), support_forward))
app.add_handler(MessageHandler(filters.ALL & filters.User(ADMIN_ID), admin_action))

print("🔥 STABLE BOT RUNNING")
app.run_polling()
