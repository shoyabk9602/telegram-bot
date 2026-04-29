from datetime import datetime, timedelta
import asyncio
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
BOT_TOKEN = "8682580574:AAHjnMcDsVU4vqw7meE7jB2pKIE024FSzVM"
SUPPORT_BOT_TOKEN = "8742370126:AAFZpYXPlsEASY4l6lABj6kgxluAqW_t5n4"
SUPPORT_CHAT_ID = 8338253309

ADMIN_ID = 8338253309

# 🔥 PRIVATE CHANNEL ID
CHANNEL_ID = -1003685301571

SUPPORT_BOT = Bot(token=SUPPORT_BOT_TOKEN)

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    link_sent INTEGER DEFAULT 0
)
""")

cursor.execute("CREATE TABLE IF NOT EXISTS msgs (user_id INTEGER, msg_id INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS tickets (user_id INTEGER PRIMARY KEY, messages TEXT)")
conn.commit()

# ================= DB FUNCTIONS =================
def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit()

def has_link(uid):
    row = cursor.execute("SELECT link_sent FROM users WHERE user_id=?", (uid,)).fetchone()
    return row and row[0] == 1

def set_link(uid):
    cursor.execute("UPDATE users SET link_sent=1 WHERE user_id=?", (uid,))
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id FROM users")
    return [x[0] for x in cursor.fetchall()]

# ================= UI =================
def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")],
        [InlineKeyboardButton("🧹 Delete", callback_data="delete")],
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
    name = user.first_name

    save_user(uid)

    if uid == ADMIN_ID:
        await update.message.reply_text("🎛️ Control Panel", reply_markup=panel())
        return

    # 🔥 already got link
    if has_link(uid):
        await update.message.reply_text(EXPIRE_MSG)
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    set_link(uid)

    username = f"@{user.username}" if user.username else "No Username"

    await SUPPORT_BOT.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text=f"📢 NEW LINK\n👤 {username}\n🆔 {uid}\n\n🔗 {link.invite_link}"
    )

    msg = await update.message.reply_text(
        f"<b>Hey 👋 {name}</b>\n\n"
        f"🔥 VIP Access Unlock!\n\n"
        f"👉 {link.invite_link}\n\n"
        f"⏳ 60 sec remaining",
        reply_markup=join_btn(),
        parse_mode="HTML"
    )

    asyncio.create_task(countdown(msg, link.invite_link, name))

# ================= EXPIRE MESSAGE =================
EXPIRE_MSG = (
"If link is expired than please contact to our Helpline for VIP channel link 👍\n\n"
"किसी भी तरह की हेल्प चाहिए तो वो भी आपकी ये सही करवा देगा \n\n"
"बहुत अच्छा होगा अगर आप एक बार में ही अपनी परेशानी लिख दोगे क्योंकि बार बार मैसेज करने से बहुत अच्छा है कि एक बार में ही परेशानी बतादो\n\n"
"Warning ⚠️ : हम किसी से भी किसी भी चीज के लिए पैसे नहीं लेते ना किसी को पैसों में टीम देते है और ना ही किसी को ये बोलकर पैसे लेते है कि हम आपके पैसे बढ़ा कर देंगे \n\n"
"अगर आप किसी को पैसे देते हो और फिर हमको मैसेज करोगे तो हम उसमें कुछ नहीं कर पाएंगे तो आप सबसे नम्र निवेदन है कि किसी को भी पैसे ना दे \n\n"
"जिनको चैनल ज्वाइन करना है वो यहां मैसेज करे 👍\n\n"
"Helpline Manager ✅\nhttps://t.me/helplineIKMXCRICKET"
)

# ================= COUNTDOWN =================
async def countdown(msg, link, name):
    for i in range(60, 0, -1):
        try:
            await msg.edit_text(
                f"<b>Hey 👋 {name}</b>\n\n"
                f"🔥 VIP Access Unlock!\n\n"
                f"👉 {link}\n\n"
                f"⏳ {i} sec remaining",
                reply_markup=join_btn(),
                parse_mode="HTML"
            )
        except:
            pass
        await asyncio.sleep(1)

    await msg.edit_text(EXPIRE_MSG)

# ================= JOIN =================
async def join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    member = await context.bot.get_chat_member(CHANNEL_ID, query.from_user.id)

    if member.status in ["member", "administrator", "creator"]:
        await query.edit_message_text("✅ Joined Successfully")
    else:
        await query.answer("❌ Join first", show_alert=True)

# ================= SUPPORT =================
async def support_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    if uid == ADMIN_ID:
        return

    text = update.message.text or "Media"

    row = cursor.execute("SELECT messages FROM tickets WHERE user_id=?", (uid,)).fetchone()

    if row:
        new_msg = row[0] + f"\n• {text}"
        cursor.execute("UPDATE tickets SET messages=? WHERE user_id=?", (new_msg, uid))
    else:
        new_msg = f"• {text}"
        cursor.execute("INSERT INTO tickets VALUES (?, ?)", (uid, new_msg))

    conn.commit()

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Solve", callback_data=f"solve_{uid}")]
    ])

    await SUPPORT_BOT.send_message(
        chat_id=SUPPORT_CHAT_ID,
        text=f"📩 QUERY\n👤 {user.first_name}\n🆔 {uid}\n\n{new_msg}",
        reply_markup=kb
    )

# ================= SOLVE =================
async def solve_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = int(query.data.split("_")[1])
    cursor.execute("DELETE FROM tickets WHERE user_id=?", (uid,))
    conn.commit()

    await query.edit_message_text("✅ Query Solved")

# ================= PANEL =================
async def panel_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    mode = query.data

    if mode == "users":
        await query.message.reply_text(f"👥 Users: {len(get_users())}")
        return

    admin_mode[ADMIN_ID] = mode
    await query.message.reply_text(f"{mode.upper()} MODE ON")

# ================= ADMIN ACTION =================
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    mode = admin_mode.get(ADMIN_ID)
    if not mode:
        return

    users = get_users()
    msg = update.message

    # DELETE
    if mode == "delete":
        data = cursor.execute("SELECT user_id, msg_id FROM msgs").fetchall()
        for u, mid in data:
            try:
                await context.bot.delete_message(chat_id=u, message_id=mid)
            except:
                pass

        cursor.execute("DELETE FROM msgs")
        conn.commit()

        await msg.reply_text("🧹 All messages deleted", reply_markup=panel())
        admin_mode[ADMIN_ID] = None
        return

    # BROADCAST
    for u in users:
        try:
            sent = await context.bot.copy_message(
                chat_id=u,
                from_chat_id=update.effective_chat.id,
                message_id=msg.message_id
            )
            cursor.execute("INSERT INTO msgs VALUES (?,?)", (u, sent.message_id))
            conn.commit()
        except:
            pass

    await msg.reply_text("✅ Broadcast Done", reply_markup=panel())
    admin_mode[ADMIN_ID] = None

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(join_check, pattern="join_check"))
app.add_handler(CallbackQueryHandler(solve_ticket, pattern="solve_"))
app.add_handler(CallbackQueryHandler(panel_click))

app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), support_forward))
app.add_handler(MessageHandler(filters.ALL & filters.User(ADMIN_ID), admin_action))

print("🔥 FINAL BOT RUNNING")
app.run_polling()
