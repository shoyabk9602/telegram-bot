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
cursor.execute("CREATE TABLE IF NOT EXISTS stats (date TEXT, links INTEGER, joins INTEGER)")
conn.commit()

# ================= HELPERS =================
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
        cursor.execute("UPDATE stats SET links = links + 1 WHERE date=?", (today(),))
    else:
        cursor.execute("INSERT INTO stats VALUES (?,1,0)", (today(),))
    conn.commit()

def add_join():
    cursor.execute("SELECT joins FROM stats WHERE date=?", (today(),))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE stats SET joins = joins + 1 WHERE date=?", (today(),))
    else:
        cursor.execute("INSERT INTO stats VALUES (?,0,1)", (today(),))
    conn.commit()

def get_stats():
    cursor.execute("SELECT links, joins FROM stats WHERE date=?", (today(),))
    row = cursor.fetchone()
    return row if row else (0, 0)

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
                f"🔥 *LIMITED ACCESS INVITE*\n\n"
                f"👉 {link}\n\n"
                f"⏳ *Expire in:* {i} sec\n\n"
                f"⚠️ Jaldi join karo warna access khatam!",
                parse_mode="Markdown",
                reply_markup=join_button()
            )
        except:
            pass
        await asyncio.sleep(1)

    await msg.edit_text(
        "❌ *ACCESS EXPIRED*\n\n"
        "🚫 Ye link ab kaam nahi karega\n\n"
        "📩 *Naya link paane ke liye message karo:*\n"
        "👉 https://t.me/Shoyabk96",
        parse_mode="Markdown"
    )

# ================= INVITE =================
async def send_link(update, context):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else "No username"

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

        asyncio.create_task(countdown(msg, link.invite_link))
        return

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
    add_link()

    links, joins = get_stats()

    await context.bot.send_message(
        ADMIN_ID,
        f"📢 New Link Generated\n👤 {username}\n🆔 {user_id}\n\n🔗 {links} | ✅ {joins}"
    )

    msg = await update.message.reply_text(
        f"🔥 *LIMITED ACCESS INVITE*\n\n"
        f"🚨 Ye private channel sabko nahi milta\n"
        f"⚡ Sirf selected users ko access mil raha hai\n\n"
        f"👉 *Tumhara personal link:*\n{link.invite_link}\n\n"
        f"⏳ *60 sec ke andar join karo*\n"
        f"❌ Forward useless hai\n\n"
        f"⚠️ *Abhi join karo warna miss ho jayega!*",
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
        add_join()

        links, joins = get_stats()

        await query.edit_message_text(
            f"🎉 Joined Successfully\n\n📊 Today\n🔗 {links} | ✅ {joins}"
        )
    else:
        await query.answer("❌ Pehle join karo", show_alert=True)

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

    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_photo(u, file_id, caption=caption)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(f"📸 Sent: {success}\n❌ Failed: {fail}")

# ================= BUTTON =================
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

    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_message(u, msg, reply_markup=kb)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(f"🔘 Sent: {success}\n❌ Failed: {fail}")

# ================= SCHEDULE =================
async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    delay = int(context.args[0])
    msg = " ".join(context.args[1:])

    await update.message.reply_text(f"⏳ Scheduled in {delay}s")

    await asyncio.sleep(delay)

    success, fail = 0, 0

    for u in get_users():
        try:
            await context.bot.send_message(u, msg)
            success += 1
            await asyncio.sleep(0.05)
        except:
            fail += 1

    await update.message.reply_text(f"⏰ Done\n✅ {success}\n❌ {fail}")

# ================= USERS =================
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"👥 Users: {len(get_users())}")

# ================= STATS =================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    links, joins = get_stats()
    await update.message.reply_text(
        f"📊 Today Stats\n\n🔗 Links: {links}\n✅ Joins: {joins}"
    )

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", send_link))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("photo", photo))
app.add_handler(CommandHandler("button", button))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(CommandHandler("users", users))
app.add_handler(CommandHandler("stats", stats))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_link))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 FINAL ALL-IN-ONE BOT RUNNING")
app.run_polling()
