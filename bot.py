from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ChatMemberHandler
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
CHANNEL_ID = "@ikminvite"

user_links = {}
joined_users = set()

# 🔹 button
def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

# 🔹 message handler
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    # 🔥 TEST MODE (only for keyword)
    if text == "shoyabtest":
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )

        await update.message.reply_text(
            f"🧪 TEST MODE ACTIVE\n\n👉 {link.invite_link}",
            reply_markup=join_button()
        )
        return

    # 👉 already joined
    if user_id in joined_users:
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    # 👉 already got link
    if user_id in user_links:
        await update.message.reply_text(
            "❌ Tum already invite link le chuke ho",
            reply_markup=join_button()
        )
        return

    # 👉 new user
    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1
    )

    user_links[user_id] = link.invite_link

    await update.message.reply_text(
        f"🚀 Join karo:\n{link.invite_link}",
        reply_markup=join_button()
    )

# 🔹 verify join
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

# 🔹 track join
async def track_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_member.new_chat_member.user
    user_id = user.id

    if update.chat_member.new_chat_member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)

# app
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(CallbackQueryHandler(check_join))
app.add_handler(ChatMemberHandler(track_join, ChatMemberHandler.CHAT_MEMBER))

print("Bot Running 🚀")
app.run_polling()
