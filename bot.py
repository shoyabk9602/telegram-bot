from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    ChatJoinRequestHandler,
    filters,
    ContextTypes
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
CHAT_ID = "https://t.me/+rqsNYHU0dxQ1MWE9"  # ⚠️ yeh ab PRIVATE GROUP hona chahiye

user_links = {}
allowed_users = set()   # jinko join allow hai
joined_users = set()

def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

# 🔹 message handler
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    # TEST MODE
    if text == "shoyabtest":
        link = await context.bot.create_chat_invite_link(
            chat_id=CHAT_ID,
            creates_join_request=True
        )
        await update.message.reply_text(
            f"🧪 TEST MODE\n👉 {link.invite_link}",
            reply_markup=join_button()
        )
        return

    if user_id in joined_users:
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    if user_id in user_links:
        await update.message.reply_text(
            f"❌ Tum already link le chuke ho\n👉 {user_links[user_id]}",
            reply_markup=join_button()
        )
        return

    # 👉 new link (join request based)
    link = await context.bot.create_chat_invite_link(
        chat_id=CHAT_ID,
        creates_join_request=True
    )

    user_links[user_id] = link.invite_link
    allowed_users.add(user_id)

    await update.message.reply_text(
        f"🚀 Join karo (request bhejo):\n{link.invite_link}\n\n⚠️ Dusre log try karein to reject honge",
        reply_markup=join_button()
    )

# 🔹 join request handler (MAIN CONTROL)
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.chat_join_request.from_user.id

    if user_id in allowed_users:
        # ✅ approve
        await context.bot.approve_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=user_id
        )
        joined_users.add(user_id)
        allowed_users.discard(user_id)

        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 Approved! Welcome 🚀"
        )
    else:
        # ❌ reject others (forwarded link users)
        await context.bot.decline_chat_join_request(
            chat_id=update.chat_join_request.chat.id,
            user_id=user_id
        )

# 🔹 optional verify button
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Request bhejo, approve hone par join ho jaoge")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(ChatJoinRequestHandler(handle_join_request))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 Secure Gate Bot Running...")
app.run_polling()
