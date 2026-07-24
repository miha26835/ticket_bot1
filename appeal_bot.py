import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from appeal_config import BOT_TOKEN, MODERATION_CHAT_ID, MODERATORS
from appeal_db import init_db, save_appeal, update_appeal_status, get_appeal

logging.basicConfig(level=logging.INFO)

# Состояния для разговора
NICK, REASON = range(2)

async def start_appeal(update: Update, context):
    await update.message.reply_text(
        "⚖️ Бот для обжалования решений администраторов\n\n"
        "Если вы не согласны с решением модератора, вы можете подать апелляцию.\n\n"
        "1️⃣ Ваш ник\n"
        "2️⃣ Причина обжалования\n\n"
        "⏱️ Среднее время ответа: 3-12 часов\n\n"
        "Напишите ваш игровой ник:"
    )
    return NICK

async def get_appeal_nick(update: Update, context):
    context.user_data['nick'] = update.message.text
    await update.message.reply_text("📝 Напишите причину обжалования:")
    return REASON

async def get_appeal_reason(update: Update, context):
    data = context.user_data
    appeal_text = (
        f"👤 Ник: {data['nick']}\n"
        f"⚖️ Обжалование: {update.message.text}\n"
        f"📩 Отправил: @{update.effective_user.username or 'нет юзера'}"
    )
    
    appeal_id = await save_appeal(
        user_id=update.effective_user.id,
        username=update.effective_user.username or "без_юзера",
        appeal_text=appeal_text
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Принять", callback_data=f"appeal_accept_{appeal_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"appeal_reject_{appeal_id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=MODERATION_CHAT_ID,
        text=f"🔔 Новая апелляция #{appeal_id}\n\n{appeal_text}",
        reply_markup=keyboard
    )

    await update.message.reply_text(
        f"✅ Апелляция #{appeal_id} принята!\n"
        "Модераторы рассмотрят её в ближайшее время.\n"
        "⏱️ Среднее время ответа: 3-12 часов."
    )
    return ConversationHandler.END

async def handle_appeal(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in MODERATORS:
        await query.edit_message_text("⛔ Нет прав!")
        return

    action, _, appeal_id_str = query.data.partition('_')
    appeal_id = int(appeal_id_str)
    appeal_info = await get_appeal(appeal_id)
    if not appeal_info:
        await query.edit_message_text("❌ Апелляция не найдена!")
        return

    user_id, _ = appeal_info
    status = "accepted" if action == "accept" else "rejected"
    await update_appeal_status(appeal_id, status)

    status_text = "✅ ПРИНЯТА" if action == "accept" else "❌ ОТКЛОНЕНА"
    await query.edit_message_text(
        f"{query.message.text}\n\nСтатус: {status_text}"
    )

    msg = "✅ Принята! Будет пересмотрено." if action == "accept" else "❌ Отклонена. Оснований нет."
    await context.bot.send_message(user_id, f"Апелляция #{appeal_id}\n{msg}")

async def cancel(update: Update, context):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_appeal)],
        states={
            NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_appeal_nick)],
            REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_appeal_reason)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_appeal, pattern='^(appeal_accept_|appeal_reject_)'))

    asyncio.run(init_db())
    print("🤖 Бот обжалований запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
