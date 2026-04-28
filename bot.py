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

# user data store
user_links = {}
joined_users = set()

# 🔹 message handler
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 👉 agar already join kar chuka hai
    if user_id in joined_users:
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    # 👉 agar link already mila hai
    if user_id in user_links:
        await update.message.reply_text(f"👆 Tumhara link:\n{user_links[user_id]}")
        return

    try:
        # 👉 new invite link
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )

        invite_link = link.invite_link

        # save
        user_links[user_id] = invite_link

        await update.message.reply_text(f"Join karo 👇\n{invite_link}")

    except Exception as e:
        print("Error:", e)


# 🔹 join detect + link expire
async def track_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_member.new_chat_member.user
    user_id = user.id

    # user joined
    if update.chat_member.new_chat_member.status in ["member", "administrator", "creator"]:
        joined_users.add(user_id)

        # 👉 link expire (revoke)
        if user_id in user_links:
            try:
                await context.bot.revoke_chat_invite_link(
                    chat_id=CHANNEL_ID,
                    invite_link=user_links[user_id]
                )
                print(f"Link expired for {user_id}")
            except Exception as e:
                print("Revoke error:", e)


# app start
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(ChatMemberHandler(track_join, ChatMemberHandler.CHAT_MEMBER))

print("Bot chal raha hai...")
app.run_polling()
