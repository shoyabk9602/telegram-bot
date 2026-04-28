from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
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

# 🔹 main message handler
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    # 🔥 TEST MODE
    if text == "shoyabtest":
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )

        await update.message.reply_text(
            f"🧪 *TEST MODE ACTIVE*\n\n👉 {link.invite_link}",
            parse_mode="Markdown",
            reply_markup=join_button()
        )
        return

    # ✅ already joined
    if user_id in joined_users:
        await update.message.reply_text(
            "✅ *Tum already join kar chuke ho*\n\n💡 Dubara link ki zarurat nahi",
            parse_mode="Markdown"
        )
        return

    # ❌ already got link
    if user_id in user_links:
        await update.message.reply_text(
            "❌ *Access Denied*\n\n🚫 Tum already invite link le chuke ho\n🔒 Dubara link generate nahi hoga",
            parse_mode="Markdown",
            reply_markup=join_button()
        )
        return

    # 🆕 new user → generate link
    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1
    )

    invite_link = link.invite_link
    user_links[user_id] = invite_link

    await update.message.reply_text(
        f"🚀 *Exclusive Invite Link*\n\n👉 {invite_link}\n\n⚠️ *Note:* Join karne ke baad niche button zaroor dabao",
        parse_mode="Markdown",
        reply_markup=join_button()
    )

# 🔹 verify join + expire link
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    member = await context.bot.get_chat_member(CHANNEL_ID, user_id)

    # ✅ user joined
    if member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)

        # 🔥 expire link
        if user_id in user_links:
            try:
                await context.bot.revoke_chat_invite_link(
                    chat_id=CHANNEL_ID,
                    invite_link=user_links[user_id]
                )
                print(f"Link expired for {user_id}")
            except Exception as e:
                print("Revoke error:", e)

        await query.edit_message_text(
            "🎉 *Successfully Joined!*\n\n🔥 Welcome to channel\n💡 Ab tum full access me ho",
            parse_mode="Markdown"
        )

        # optional DM
        await context.bot.send_message(
            chat_id=user_id,
            text="🔥 Welcome! Stay tuned for updates 😎"
        )

    else:
        await query.answer("❌ Pehle channel join karo", show_alert=True)

# 🔹 start app
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 Advanced Bot Running...")
app.run_polling()
