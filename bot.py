from datetime import datetime, timedelta
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
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

# 🔥 countdown
async def countdown_timer(message, invite_link, seconds):
    for remaining in range(seconds, 0, -1):
        try:
            await message.edit_text(
                f"🚀 *Exclusive Invite Link*\n\n"
                f"👉 {invite_link}\n\n"
                f"⏳ Expire in: *{remaining} sec*\n\n"
                f"👉 Join karke button dabao",
                parse_mode="Markdown",
                reply_markup=join_button()
            )
            await asyncio.sleep(1)
        except:
            await asyncio.sleep(1)

    # 🔥 expire message
    try:
        await message.edit_text(
            "❌ *LINK EXPIRED*\n\n"
            "⛔ Ye invite link ab kaam nahi karega\n\n"
            "📢 *Next Step:*\n"
            "👉 Naya link lene ke liye yahan message kare\n"
            "🔗 https://t.me/Shoyabk96",
            parse_mode="Markdown"
        )
    except:
        pass


# 🔹 main logic
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.lower() if update.message.text else ""

    # 🧪 TEST MODE
    if text == "shoyabtest":
        link = await context.bot.create_chat_invite_link(
            chat_id=CHANNEL_ID,
            member_limit=1,
            expire_date=datetime.utcnow() + timedelta(seconds=60)
        )

        msg = await update.message.reply_text(
            f"🧪 *TEST MODE ACTIVE*\n\n👉 {link.invite_link}",
            parse_mode="Markdown",
            reply_markup=join_button()
        )

        asyncio.create_task(countdown_timer(msg, link.invite_link, 60))
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

    # 🆕 new link
    link = await context.bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        expire_date=datetime.utcnow() + timedelta(seconds=60)
    )

    invite_link = link.invite_link
    user_links[user_id] = invite_link

    msg = await update.message.reply_text(
        f"🚀 *Exclusive Invite Link*\n\n👉 {invite_link}\n\n"
        f"⚠️ *Note:* 60 sec ke andar join kare",
        parse_mode="Markdown",
        reply_markup=join_button()
    )

    asyncio.create_task(countdown_timer(msg, invite_link, 60))


# 🔹 START COMMAND (AUTO LINK TRIGGER)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome!*\n\n🔥 Yahan se apna exclusive invite link pao",
        parse_mode="Markdown"
    )

    # 🔥 direct link bhej do
    await auto_reply(update, context)


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

        await query.edit_message_text(
            "🎉 *Successfully Joined!*\n\n🔥 Welcome!",
            parse_mode="Markdown"
        )

        await context.bot.send_message(
            chat_id=user_id,
            text="🔥 Welcome! Stay tuned 😎"
        )
    else:
        await query.answer("❌ Pehle channel join karo", show_alert=True)


# 🚀 app start
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))  # 🔥 important
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply))
app.add_handler(CallbackQueryHandler(check_join))

print("🔥 Final Bot Running...")
app.run_polling()
