from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
CHANNEL_ID = "@ikminvite"

# user tracking
used_users = {}

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 👉 agar user pehle hi link le chuka hai
    if user_id in used_users:
        await update.message.reply_text(f"👆 Tumhara link:\n{used_users[user_id]}")
        return

    try:
        # 👉 NEW UNIQUE LINK (IMPORTANT)
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            creates_join_request=False
        )

        invite_link = link.invite_link

        # save link
        used_users[user_id] = invite_link

        await update.message.reply_text(f"Join karo 👇\n{invite_link}")

    except Exception as e:
        print("Error:", e)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

print("Bot chal raha hai...")
app.run_polling()
