import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from main_config import BOT_TOKEN, MODERATION_CHAT_ID, MODERATORS
from main_db import init_db, save_ticket, update_ticket_status, get_ticket

logging.basicConfig(level=logging.INFO)

# Состояния для ConversationHandler
NICK, VIOLATION, PROOF = range(3)

async def start(update: Update, context):
    await update.message.reply_text(
        "🛡️ Добро пожаловать в систему тикетов!\n\n"
        "1️⃣ Ник нарушителя\n2️⃣ Что он делал\n3️⃣ Запись нарушения\n\nНапиши ник:"
    )
    return NICK

async def get_nick(update: Update, context):
    context.user_data['nick'] = update.message.text
    await update.message.reply_text("📝 Опиши нарушение:")
    return VIOLATION

async def get_violation(update: Update, context):
    context.user_data['violation'] = update.message.text
    await update.message.reply_text("📎 Пришли доказательство:")
    return PROOF

async def get_proof(update: Update, context):
    data = context.user_data
    proof = "Файл/медиа"
    if update.message.photo:
        proof = f"Фото: {update.message.photo[-1].file_id}"
    elif update.message.video:
        proof = f"Видео: {update.message.video.file_id}"
    elif update.message.document:
        proof = f"Файл: {update.message.document.file_id}"
    elif update.message.text:
        proof = update.message.text

    ticket_text = (
        f"👤 Нарушитель: {data['nick']}\n"
        f"⚡ Нарушение: {data['violation']}\n"
        f"📎 Доказательство: {proof}\n"
        f"📩 Отправил: @{update.effective_user.username or 'нет юзера'}"
    )
    ticket_id = await save_ticket(
        user_id=update.effective_user.id,
        username=update.effective_user.username or "без_юзера",
        ticket_text=ticket_text
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Принять", callback_data=f"accept_{ticket_id}"),
         InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{ticket_id}")]
    ])

    await context.bot.send_message(
        chat_id=MODERATION_CHAT_ID,
        text=f"🔔 Новый тикет #{ticket_id}\n\n{ticket_text}",
        reply_markup=keyboard
    )

    await update.message.reply_text(f"✅ Тикет #{ticket_id} принят! Модераторы рассмотрят.")
    return ConversationHandler.END

async def handle_moderation(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in MODERATORS:
        await query.edit_message_text("⛔ Нет прав!")
        return

    action, ticket_id_str = query.data.split('_')
    ticket_id = int(ticket_id_str)
    ticket_info = await get_ticket(ticket_id)
    if not ticket_info:
        await query.edit_message_text("❌ Тикет не найден!")
        return

    user_id, _ = ticket_info
    status = "accepted" if action == "accept" else "rejected"
    await update_ticket_status(ticket_id, status)

    status_text = "✅ ПРИНЯТ" if action == "accept" else "❌ ОТКЛОНЁН"
    await query.edit_message_text(
        f"{query.message.text}\n\nСтатус: {status_text}"
    )

    msg = "✅ Принят! Игрок получит наказание." if action == "accept" else "❌ Отклонён. Недостаточно доказательств."
    await context.bot.send_message(user_id, f"Тикет #{ticket_id}\n{msg}")

async def cancel(update: Update, context):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_nick)],
            VIOLATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_violation)],
            PROOF: [MessageHandler(filters.ALL, get_proof)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_moderation, pattern='^(accept_|reject_)'))

    asyncio.run(init_db())
    print("🤖 Основной бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
