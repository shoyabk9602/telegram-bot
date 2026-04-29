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
cursor.execute("CREATE TABLE IF NOT EXISTS msgs (user_id INTEGER, msg_id INTEGER)")
conn.commit()

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
    cursor.execute("SELECT got_link FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0] == 1

def set_join(uid):
    cursor.execute("UPDATE users SET joined=1 WHERE user_id=?", (uid,))
    conn.commit()

def has_join(uid):
    cursor.execute("SELECT joined FROM users WHERE user_id=?", (uid,))
    return cursor.fetchone()[0] == 1

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
        [InlineKeyboardButton("📸 Photo", callback_data="photo")],
        [InlineKeyboardButton("🎬 Video", callback_data="video")],
        [InlineKeyboardButton("🎧 Audio/Voice", callback_data="audio")],
        [InlineKeyboardButton("🧹 Delete All", callback_data="delete")],
        [InlineKeyboardButton("👥 Users", callback_data="users")]
    ])

user_mode = {}

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

    if uid == ADMIN_ID:
        await update.message.reply_text("🎛️ Control Panel", reply_markup=panel())
        return

    # 🔥 FIX: already joined → NO LINK AGAIN
    if has_join(uid):
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    if has_link(uid):
        await update.message.reply_text("❌ Tum already link le chuke ho\nJoin karo pehle")
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

# ================= CUSTOM USER MSG =================
async def user_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        return

    await update.message.reply_text(
        "❗ Agar koi problem ho to yahan msg karo 👇\n👉 @Shoyabk96"
    )

# ================= COUNTDOWN =================
async def countdown(msg, link):
    for i in range(60, 0, -1):
        try:
            await msg.edit_text(f"👉 {link}\n⏳ {i}s", reply_markup=join_btn())
        except:
            pass
        await asyncio.sleep(1)

    await msg.edit_text("❌ Link expired\n👉 @Shoyabk96")

# ================= JOIN FIX =================
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

# ================= PANEL CLICK =================
async def panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    if uid != ADMIN_ID:
        return

    user_mode[uid] = query.data

    if query.data == "users":
        await query.message.reply_text(f"👥 {len(get_users())} users")
        return

    await query.message.reply_text(f"👉 {query.data.upper()} mode ON")

# ================= HANDLE ADMIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        return

    mode = user_mode.get(uid)
    if not mode:
        return

    caption = update.message.caption or update.message.text or ""

    success, fail = 0, 0

    for u in get_users():
        try:
            if mode == "broadcast":
                msg = await context.bot.send_message(u, caption)

            elif mode == "photo" and update.message.photo:
                msg = await context.bot.send_photo(u, update.message.photo[-1].file_id, caption=caption)

            elif mode == "video" and update.message.video:
                msg = await context.bot.send_video(u, update.message.video.file_id, caption=caption)

            elif mode == "audio":
                if update.message.audio:
                    msg = await context.bot.send_audio(u, update.message.audio.file_id, caption=caption)
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

    await update.message.reply_text(f"✅ Sent: {success}\n❌ Failed: {fail}", reply_markup=panel())
    user_mode[uid] = None

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(join_check, pattern="join_check"))
app.add_handler(CallbackQueryHandler(panel_click))

# 🔥 FIX: user custom reply
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_reply))

# 🔥 admin handler
app.add_handler(MessageHandler(filters.ALL, handle))

print("🔥 FINAL PERFECT BOT RUNNING")
app.run_polling()
