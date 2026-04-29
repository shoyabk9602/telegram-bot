from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
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

# ================= PANEL =================
def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("📸 Photo/Album", callback_data="photo")],
        [InlineKeyboardButton("🎬 Video/Album", callback_data="video")],
        [InlineKeyboardButton("🧹 Delete All", callback_data="delete")]
    ])

user_mode = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    save_user(uid)

    if uid == ADMIN_ID:
        await update.message.reply_text("🎛️ Panel", reply_markup=panel())

# ================= PANEL =================
async def panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    user_mode[query.from_user.id] = query.data
    await query.message.reply_text(f"{query.data.upper()} MODE ON")

# ================= HANDLE =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid != ADMIN_ID:
        return

    mode = user_mode.get(uid)
    if not mode:
        return

    success, fail = 0, 0

    # 🔥 DELETE SYSTEM
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

    # ================= MULTI PHOTO =================
    if mode == "photo" and update.message.media_group_id:
        media_group = context.user_data.get("album", [])
        media_group.append(update.message)

        context.user_data["album"] = media_group

        await asyncio.sleep(1)

        if len(context.user_data["album"]) > 0:
            media = []
            for m in context.user_data["album"]:
                media.append(InputMediaPhoto(m.photo[-1].file_id))

            for u in get_users():
                try:
                    msgs = await context.bot.send_media_group(u, media)
                    for msg in msgs:
                        save_msg(u, msg.message_id)
                    success += 1
                except:
                    fail += 1

            context.user_data["album"] = []
            await update.message.reply_text("📸 Album Sent")

    # ================= MULTI VIDEO =================
    elif mode == "video" and update.message.media_group_id:
        media_group = context.user_data.get("album", [])
        media_group.append(update.message)

        context.user_data["album"] = media_group

        await asyncio.sleep(1)

        if len(context.user_data["album"]) > 0:
            media = []
            for m in context.user_data["album"]:
                media.append(InputMediaVideo(m.video.file_id))

            for u in get_users():
                try:
                    msgs = await context.bot.send_media_group(u, media)
                    for msg in msgs:
                        save_msg(u, msg.message_id)
                    success += 1
                except:
                    fail += 1

            context.user_data["album"] = []
            await update.message.reply_text("🎬 Video Album Sent")

    # ================= SINGLE =================
    else:
        for u in get_users():
            try:
                if mode == "broadcast":
                    msg = await context.bot.send_message(u, update.message.text)

                elif mode == "photo" and update.message.photo:
                    msg = await context.bot.send_photo(u, update.message.photo[-1].file_id)

                elif mode == "video" and update.message.video:
                    msg = await context.bot.send_video(u, update.message.video.file_id)

                save_msg(u, msg.message_id)
                success += 1
            except:
                fail += 1

        await update.message.reply_text(f"✅ Sent: {success} ❌ {fail}")

    user_mode[uid] = None

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(panel_click))
app.add_handler(MessageHandler(filters.ALL, handle))

print("🔥 MULTI MEDIA BOT READY")
app.run_polling()
