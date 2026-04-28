from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
    ChatMemberHandler
)

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
CHANNEL_ID = "@ikminvite"

user_links = {}
joined_users = set()

# 🔹 stylish messages
ALREADY_MSG = """❌ *Access Denied*

🚫 Tum already invite link le chuke ho  
🔒 Dubara link generate nahi hoga

👉 Agar join nahi kiya hai, to apna pehla link use karo"""

JOINED_MSG = """✅ *Successfully Joined*

🎉 Tum channel join kar chuke ho  
💡 Ab dubara link ki zarurat nahi"""

# 🔹 message handler
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 👉 already joined
    if user_id in joined_users:
        await update.message.reply_text(JOINED_MSG, parse_mode="Markdown")
        return

    # 👉 already got link
    if user_id in user_links:
        await update.message.reply_text(ALREADY_MSG, parse_mode="Markdown")
        return

    try:
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )

        invite_link = link.invite_link
        user_links[user_id] = invite_link

        await update.message.reply_text(
            f"🚀 *Exclusive Invite Link*\n\n👉 {invite_link}\n\n⚠️ *Note:* Ye link sirf ek baar use hoga",
            parse_mode="Markdown"
        )

    except Exception as e:
        print("Error:", e)


# 🔹 join detect + expire link
async def track_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_member.new_chat_member.user
    user_id = user.id

    if update.chat_member.new_chat_member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)

        if user_id in user_links:
            try:
                await context.bot.revoke_chat_invite_link(
                    chat_id=CHANNEL_ID,
                    invite_link=user_links[user_id]
                )
            except Exception as e:
                print("Revoke error:", e)


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(ChatMemberHandler(track_join, ChatMemberHandler.CHAT_MEMBER))

print("Bot chal raha hai...")
app.run_polling()
