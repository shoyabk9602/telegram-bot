from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 👉 Yaha apna FULL token daal (BotFather wala)
BOT_TOKEN = "8640066413:AAEjpnv1DMFsux3mhGkT6EoS1-_zY51uz8A"

# 👉 Tera channel username
CHANNEL_ID = "@ikminvite"

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # unique 1-user invite link
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )

        await update.message.reply_text(
            f"Join karo 👇\n{link.invite_link}"
        )

    except Exception as e:
        print("Error:", e)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply)
    )

    print("Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
