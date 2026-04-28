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

    if user_id in joined_users:
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    if user_id in user_links:
        await update.message.reply_text(
            f"❌ Tum already link le chuke ho\n\n👉 {user_links[user_id]}",
            reply_markup=join_button()
        )
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1
    )

    user_links[user_id] = link.invite_link

    await update.message.reply_text(
        f"🚀 Join karo:\n{link.invite_link}\n\n⚠️ Ek hi baar use hoga",
        reply_markup=join_button()
    )

# 🔹 join verify button
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    if member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)

        # expire link
        if user_id in user_links:
            try:
                await context.bot.revoke_chat_invite_link(
                    chat_id=CHANNEL_ID,
                    invite_link=user_links[user_id]
                )
            except:
                pass

        await query.edit_message_text("🎉 Welcome! Tum successfully join kar chuke ho 🚀")

        # DM welcome
        await context.bot.send_message(
            chat_id=user_id,
            text="🔥 Welcome to premium system!\nStay tuned 😎"
        )

    else:
        await query.answer("❌ Pehle channel join karo", show_alert=True)

# 🔹 join detect auto
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

print("Advanced Bot Running 🚀")
app.run_polling()
