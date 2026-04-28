from datetime import datetime, timedelta
import asyncio
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

def join_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
    ])

# 🔥 countdown function
async def countdown_timer(message, invite_link, seconds):
    for remaining in range(seconds, 0, -5):
        try:
            await message.edit_text(
                f"🚀 *Exclusive Invite Link*\n\n👉 {invite_link}\n\n⏳ Expire in: *{remaining} sec*\n\n👉 Join karke button dabao",
                parse_mode="Markdown",
                reply_markup=join_button()
            )
            await asyncio.sleep(5)
        except:
            break

    # final expire message
    try:
        await message.edit_text(
            "❌ *Link Expired*\n\n🔒 Ab ye link kaam nahi karega\n👉 Naya link nahi milega",
            parse_mode="Markdown"
        )
    except:
        pass


async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower()

    # TEST MODE
    if text == "shoyabtest":
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=datetime.utcnow() + timedelta(seconds=60)
        )

        msg = await update.message.reply_text(
            f"🧪 TEST MODE\n\n👉 {link.invite_link}",
            reply_markup=join_button()
        )

        asyncio.create_task(countdown_timer(msg, link.invite_link, 60))
        return

    if user_id in joined_users:
        await update.message.reply_text("✅ Tum already join kar chuke ho")
        return

    if user_id in user_links:
        await update.message.reply_text("❌ Tum already link le chuke ho")
        return

    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    user_links[user_id] = link.invite_link

    msg = await update.message.reply_text(
        f"🚀 Join karo:\n{link.invite_link}",
        reply_markup=join_button()
    )

    # 🔥 start countdown
    asyncio.create_task(countdown_timer(msg, link.invite_link, 60))


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


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 Countdown Bot Running...")
app.run_polling()
