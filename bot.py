from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
CHANNEL_ID = "@ikminvite"
ADMIN_ID = 7206670618

# ================= DATABASE =================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")
conn.commit()

def save_user(user_id):
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    except:
        pass

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# ================= DATA =================
user_links = {}
joined_users = set()

# ================= BUTTON =================
def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

# ================= COUNTDOWN (FIXED) =================
async def countdown_timer(message, invite_link, seconds):
    for remaining in range(seconds, 0, -1):
        try:
            await message.edit_text(
                f"🚀 *Exclusive Invite Link*\n\n"
                f"👉 {invite_link}\n\n"
                f"⏳ Expire in: *{remaining} sec*\n\n"
                f"👉 Join karke button dabao",
                parse_mode="Markdown",
                reply_markup=join_button()
            )
        except:
            pass
        await asyncio.sleep(1)

    # 🔥 FINAL MESSAGE (FIXED - ALWAYS SHOW)
    try:
        await message.edit_text(
            "❌ *LINK EXPIRED*\n\n"
            "⛔ Ye invite link ab kaam nahi karega\n\n"
            "📢 *Naya link lene ke liye yahan message kare:*\n"
            "👉 https://t.me/Shoyabk96",
            parse_mode="Markdown"
        )
    except Exception as e:
        print("Expire error:", e)

# ================= INVITE =================
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)

    text = update.message.text.lower() if update.message.text else ""

    # TEST MODE
    if text == "shoyabtest":
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=datetime.utcnow() + timedelta(seconds=60)
        )

        msg = await update.message.reply_text(
            f"🧪 TEST MODE\n👉 {link.invite_link}",
            reply_markup=join_button()
        )

        asyncio.create_task(countdown_timer(msg, link.invite_link, 60))
        return

    if user_id in joined_users:
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    if user_id in user_links:
        await update.message.reply_text("❌ Tum already link le chuke ho", reply_markup=join_button())
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    user_links[user_id] = link.invite_link

    msg = await update.message.reply_text(
        f"🚀 Join karo:\n{link.invite_link}",
        reply_markup=join_button()
    )

    asyncio.create_task(countdown_timer(msg, link.invite_link, 60))

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id)

    await update.message.reply_text("👋 Welcome!\n\n🔥 Link generate ho raha hai...")

    await auto_reply(update, context)

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

        await query.edit_message_text("🎉 Joined Successfully 🚀")
    else:
        await query.answer("❌ Pehle join karo", show_alert=True)

# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ Message likho")
        return

    msg = " ".join(context.args)
    users = get_users()

    success = 0
    fail = 0

    await update.message.reply_text(f"🚀 Sending to {len(users)} users...")

    for user in users:
        try:
            await context.bot.send_message(chat_id=user, text=msg)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(f"✅ Done\n✔️ {success}\n❌ {fail}")

# ================= USERS =================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"👥 Total Users: {len(get_users())}")

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("users", users))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 FINAL SYSTEM RUNNING...")
app.run_polling()
