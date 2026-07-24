import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main_config import BOT_TOKEN, MODERATION_CHAT_ID, MODERATORS
from main_db import init_db, save_ticket, update_ticket_status, get_ticket

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

user_data = {}

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "🛡️ <b>Добро пожаловать в систему тикетов!</b>\n\n"
        "1️⃣ Ник нарушителя\n2️⃣ Что он делал\n3️⃣ Запись нарушения\n\nНапиши ник:",
        parse_mode="HTML"
    )
    user_data[message.from_user.id]['step'] = 'nick'

@dp.message_handler(lambda msg: user_data.get(msg.from_user.id, {}).get('step') == 'nick')
async def get_nick(message: types.Message):
    user_data[message.from_user.id]['nick'] = message.text.strip()
    user_data[message.from_user.id]['step'] = 'violation'
    await message.answer("📝 Опиши нарушение:", parse_mode="HTML")

@dp.message_handler(lambda msg: user_data.get(msg.from_user.id, {}).get('step') == 'violation')
async def get_violation(message: types.Message):
    user_data[message.from_user.id]['violation'] = message.text.strip()
    user_data[message.from_user.id]['step'] = 'proof'
    await message.answer("📎 Пришли доказательство:", parse_mode="HTML")

@dp.message_handler(lambda msg: user_data.get(msg.from_user.id, {}).get('step') == 'proof', content_types=types.ContentTypes.ANY)
async def get_proof(message: types.Message):
    data = user_data[message.from_user.id]
    proof = "Файл/медиа"
    if message.photo:
        proof = f"Фото: {message.photo[-1].file_id}"
    elif message.video:
        proof = f"Видео: {message.video.file_id}"
    elif message.document:
        proof = f"Файл: {message.document.file_id}"
    elif message.text:
        proof = message.text

    ticket_text = (
        f"👤 <b>Нарушитель:</b> {data['nick']}\n"
        f"⚡ <b>Нарушение:</b> {data['violation']}\n"
        f"📎 <b>Доказательство:</b> {proof}\n"
        f"📩 <b>Отправил:</b> @{message.from_user.username or 'нет юзера'}"
    )
    ticket_id = await save_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username or "без_юзера",
        ticket_text=ticket_text
    )

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Принять", callback_data=f"accept_{ticket_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{ticket_id}")
    )

    await bot.send_message(
        chat_id=MODERATION_CHAT_ID,
        text=f"🔔 <b>Новый тикет #{ticket_id}</b>\n\n{ticket_text}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await message.answer(f"✅ Тикет #{ticket_id} принят! Модераторы рассмотрят.", parse_mode="HTML")
    del user_data[message.from_user.id]

@dp.callback_query_handler(lambda cb: cb.data.startswith('accept_') or cb.data.startswith('reject_'))
async def handle_moderation(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in MODERATORS:
        await callback_query.answer("⛔ Нет прав!", show_alert=True)
        return

    action, ticket_id_str = callback_query.data.split('_')
    ticket_id = int(ticket_id_str)
    ticket_info = await get_ticket(ticket_id)
    if not ticket_info:
        await callback_query.answer("❌ Тикет не найден!", show_alert=True)
        return

    user_id, _ = ticket_info
    status = "accepted" if action == "accept" else "rejected"
    await update_ticket_status(ticket_id, status)

    await callback_query.message.edit_reply_markup(reply_markup=None)
    status_text = "✅ ПРИНЯТ" if action == "accept" else "❌ ОТКЛОНЁН"
    await callback_query.message.edit_text(
        f"{callback_query.message.text}\n\n<b>Статус:</b> {status_text}",
        parse_mode="HTML"
    )

    msg = "✅ Принят! Игрок получит наказание." if action == "accept" else "❌ Отклонён. Недостаточно доказательств."
    await bot.send_message(user_id, f"<b>Тикет #{ticket_id}</b>\n{msg}", parse_mode="HTML")
    await callback_query.answer(f"✅ #{ticket_id} {status_text}")

async def main():
    await init_db()
    print("🤖 Основной бот запущен!")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
