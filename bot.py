from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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
conn.commit()

def save_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

# ================= DATA =================
user_links = {}
joined_users = set()

def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

# ================= COUNTDOWN =================
async def countdown(msg, link):
    for i in range(60, 0, -1):
        try:
            await msg.edit_text(
                f"🔥 *Exclusive Invite Link*\n\n"
                f"👉 {link}\n\n"
                f"⏳ Expire in: *{i} sec*\n\n"
                f"⚠️ Join fast and press button",
                parse_mode="Markdown",
                reply_markup=join_button()
            )
        except:
            pass
        await asyncio.sleep(1)

    # 🔥 FINAL EXPIRE MESSAGE
    try:
        await msg.edit_text(
            "❌ *LINK EXPIRED*\n\n"
            "📩 Naya link lene ke liye yahan message karo:\n"
            "👉 https://t.me/Shoyabk96",
            parse_mode="Markdown"
        )
    except:
        pass

# ================= INVITE =================
async def send_link(update, context):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No username"

    save_user(user_id)

    if user_id in joined_users:
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    if user_id in user_links:
        await update.message.reply_text("❌ Tum already link le chuke ho")
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    user_links[user_id] = link.invite_link

    # 🔔 ADMIN NOTIFICATION
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 User Took Link\n👤 {username}\n🆔 {user_id}"
    )

    msg = await update.message.reply_text(
        f"🚀 *Your Private Invite Link*\n\n👉 {link.invite_link}",
        parse_mode="Markdown",
        reply_markup=join_button()
    )

    asyncio.create_task(countdown(msg, link.invite_link))

# ================= VERIFY =================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    if member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)

        if user_id in user_links:
            try:
                await context.bot.revoke_chat_invite_link(
                    chat_id=CHANNEL_ID,
                    invite_link=user_links[user_id]
                )
            except:
                pass

        await query.edit_message_text("🎉 Joined Successfully")
    else:
        await query.answer("❌ Join channel first", show_alert=True)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_link(update, context)

# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_message(u, msg)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(f"📊 Sent: {success}\n❌ Failed: {fail}")

# ================= PHOTO =================
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Photo pe reply karo")
        return

    file_id = update.message.reply_to_message.photo[-1].file_id
    caption = " ".join(context.args)

    for u in get_users():
        try:
            await context.bot.send_photo(u, file_id, caption=caption)
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text("📸 Photo sent")

# ================= BUTTON BROADCAST =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Use: /button msg link")
        return

    msg = context.args[0]
    link = context.args[1]

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👉 Click Here", url=link)]
    ])

    for u in get_users():
        try:
            await context.bot.send_message(u, msg, reply_markup=kb)
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text("🔘 Button sent")

# ================= USERS =================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"👥 Users: {len(get_users())}")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("photo", photo))
app.add_handler(CommandHandler("button", button))
app.add_handler(CommandHandler("users", users))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_link))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 FINAL PERFECT BOT RUNNING")
app.run_polling()
