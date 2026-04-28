from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"
CHANNEL_ID = "@ikminvite"

# 👉 yaha hum users store karenge
used_users = set()

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 👉 agar user pehle hi link le chuka hai
    if user_id in used_users:
        await update.message.reply_text("❌ Tum already join link le chuke ho")
        return

    try:
        # 👉 naya unique link
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )

        await update.message.reply_text(f"Join karo 👇\n{link.invite_link}")

        # 👉 user ko mark kar diya
        used_users.add(user_id)

    except Exception as e:
        print("Error:", e)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

print("Bot chal raha hai...")
app.run_polling()
