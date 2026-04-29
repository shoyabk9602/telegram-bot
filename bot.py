from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
SUPPORT_BOT_TOKEN = "8671275232:AAFTsTt6ddtLX-0qKlM8knoFVLbRN6GkIW0"
SUPPORT_CHAT_ID = 7206670618

ADMIN_ID = 7206670618
CHANNEL_ID = "@ikminvite"

# ================= SUPPORT BOT =================
SUPPORT_BOT = Bot(token=SUPPORT_BOT_TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
got_link INTEGER DEFAULT 0,
joined INTEGER DEFAULT 0
)
""")

cursor.execute("CREATE TABLE IF NOT EXISTS msgs (user_id INTEGER, msg_id INTEGER)")
conn.commit()

# ================= DB =================
def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

def set_link(uid):
    cursor.execute("UPDATE users SET got_link=1 WHERE user_id=?", (uid,))
    conn.commit()

def has_link(uid):
    row = cursor.execute("SELECT got_link FROM users WHERE user_id=?", (uid,)).fetchone()
    return row and row[0] == 1

def set_join(uid):
    cursor.execute("UPDATE users SET joined=1 WHERE user_id=?", (uid,))
    conn.commit()

def has_join(uid):
    row = cursor.execute("SELECT joined FROM users WHERE user_id=?", (uid,)).fetchone()
    return row and row[0] == 1

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
        [InlineKeyboardButton("📸 Photo/Album", callback_data="photo")],
        [InlineKeyboardButton("🎬 Video/Album", callback_data="video")],
        [InlineKeyboardButton("🎧 Audio/Voice", callback_data="audio")],
        [InlineKeyboardButton("🧹 Delete All", callback_data="delete")],
        [InlineKeyboardButton("👥 Users", callback_data="users")]
    ])

def join_btn():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="join_check")]
    ])

admin_mode = {}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    username = f"@{user.username}" if user.username else "NoUsername"

    save_user(uid)

    if uid == ADMIN_ID:
        await update.message.reply_text("🎛️ Control Panel", reply_markup=panel())
        return

    if has_join(uid):
        await update.message.reply_text("✅ Already joined")
        return

    if has_link(uid):
        await update.message.reply_text("❌ Already got link")
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    set_link(uid)

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
            await msg.edit_text(f"👉 {link}\n⏳ {i}s", reply_markup=join_btn())
        except:
            pass
        await asyncio.sleep(1)

    await msg.edit_text("❌ Link expired\n👉 @Shoyabk96")

# ================= JOIN =================
async def join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    member = await context.bot.get_chat_member(CHANNEL_ID, uid)

    if member.status in ["member", "administrator", "creator"]:
        set_join(uid)
        await query.edit_message_text("🎉 Joined Successfully")
    else:
        await query.answer("❌ Join first", show_alert=True)

# ================= SUPPORT =================
async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id == ADMIN_ID:
        return

    text = update.message.text or update.message.caption or "Media"

    msg = (
        f"📩 SUPPORT MSG\n\n"
        f"👤 @{user.username}\n"
        f"🆔 ID:{user.id}\n\n"
        f"{text}"
    )

    await SUPPORT_BOT.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text=msg
    )

# ================= PANEL =================
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

    users = get_users()
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
        admin_mode[ADMIN_ID] = None
        return

    # MULTI ALBUM
    if update.message.media_group_id:
        await asyncio.sleep(1)
        album = context.user_data.get("album", [])
        album.append(update.message)
        context.user_data["album"] = album

        media = []
        for m in album:
            if m.photo:
                media.append(InputMediaPhoto(m.photo[-1].file_id))
            elif m.video:
                media.append(InputMediaVideo(m.video.file_id))

        for u in users:
            try:
                msgs = await context.bot.send_media_group(u, media)
                for msg in msgs:
                    save_msg(u, msg.message_id)
                success += 1
            except:
                fail += 1

        context.user_data["album"] = []
        await update.message.reply_text(f"📦 Album Sent {success}")
        admin_mode[ADMIN_ID] = None
        return

    # SINGLE
    for u in users:
        try:
            if mode == "broadcast":
                msg = await context.bot.send_message(u, update.message.text)

            elif mode == "photo" and update.message.photo:
                msg = await context.bot.send_photo(u, update.message.photo[-1].file_id)

            elif mode == "video" and update.message.video:
                msg = await context.bot.send_video(u, update.message.video.file_id)

            elif mode == "audio":
                if update.message.audio:
                    msg = await context.bot.send_audio(u, update.message.audio.file_id)
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

    await update.message.reply_text(f"✅ {success} ❌ {fail}", reply_markup=panel())
    admin_mode[ADMIN_ID] = None

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

# BUTTON FIX
app.add_handler(CallbackQueryHandler(join_check, pattern="join_check"))
app.add_handler(CallbackQueryHandler(panel_click))

# SUPPORT
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), support_forward))

# ADMIN
app.add_handler(MessageHandler(filters.ALL & filters.User(ADMIN_ID), admin_action))

print("🔥 FINAL BOT RUNNING")
app.run_polling()
