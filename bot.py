import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("8671275232:AAGJsfszi4A5f4LdbDlPk2GQw7ZJCI4dqcw")
CHANNEL_ID = "@ikminvite"

async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1
        )
        await update.message.reply_text(f"Join karo 👇\n{link.invite_link}")
    except Exception as e:
        print(e)

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))

print("Bot chal raha hai...")
app.run_polling()
