import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from appeal_config import BOT_TOKEN, MODERATION_CHAT_ID, MODERATORS
from appeal_db import init_db, save_appeal, update_appeal_status, get_appeal

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

user_data = {}

@dp.message_handler(commands=['start'])
async def start_appeal(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer(
        "⚖️ <b>Обжалование решений</b>\n\n1️⃣ Ваш ник\n2️⃣ Причина обжалования\n\n⏱️ Ответ: 3-12 часов\n\nНапиши ник:",
        parse_mode="HTML"
    )
    user_data[message.from_user.id]['step'] = 'nick'

@dp.message_handler(lambda msg: user_data.get(msg.from_user.id, {}).get('step') == 'nick')
async def get_appeal_nick(message: types.Message):
    user_data[message.from_user.id]['nick'] = message.text.strip()
    user_data[message.from_user.id]['step'] = 'reason'
    await message.answer("📝 Напиши причину обжалования:", parse_mode="HTML")

@dp.message_handler(lambda msg: user_data.get(msg.from_user.id, {}).get('step') == 'reason')
async def get_appeal_reason(message: types.Message):
    data = user_data[message.from_user.id]
    appeal_text = (
        f"👤 <b>Ник:</b> {data['nick']}\n"
        f"⚖️ <b>Обжалование:</b> {message.text.strip()}\n"
        f"📩 <b>Отправил:</b> @{message.from_user.username or 'нет юзера'}"
    )
    appeal_id = await save_appeal(
        user_id=message.from_user.id,
        username=message.from_user.username or "без_юзера",
        appeal_text=appeal_text
    )

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Принять", callback_data=f"appeal_accept_{appeal_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"appeal_reject_{appeal_id}")
    )

    await bot.send_message(
        chat_id=MODERATION_CHAT_ID,
        text=f"🔔 <b>Новая апелляция #{appeal_id}</b>\n\n{appeal_text}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    await message.answer(f"✅ Апелляция #{appeal_id} принята! Ответ 3-12 часов.", parse_mode="HTML")
    del user_data[message.from_user.id]

@dp.callback_query_handler(lambda cb: cb.data.startswith('appeal_accept_') or cb.data.startswith('appeal_reject_'))
async def handle_appeal(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in MODERATORS:
        await callback_query.answer("⛔ Нет прав!", show_alert=True)
        return

    action, _, appeal_id_str = callback_query.data.partition('_')
    appeal_id = int(appeal_id_str)
    appeal_info = await get_appeal(appeal_id)
    if not appeal_info:
        await callback_query.answer("❌ Апелляция не найдена!", show_alert=True)
        return

    user_id, _ = appeal_info
    status = "accepted" if action == "accept" else "rejected"
    await update_appeal_status(appeal_id, status)

    await callback_query.message.edit_reply_markup(reply_markup=None)
    status_text = "✅ ПРИНЯТА" if action == "accept" else "❌ ОТКЛОНЕНА"
    await callback_query.message.edit_text(
        f"{callback_query.message.text}\n\n<b>Статус:</b> {status_text}",
        parse_mode="HTML"
    )

    msg = "✅ Принята! Будет пересмотрено." if action == "accept" else "❌ Отклонена. Оснований нет."
    await bot.send_message(user_id, f"<b>Апелляция #{appeal_id}</b>\n{msg}", parse_mode="HTML")
    await callback_query.answer(f"✅ #{appeal_id} {status_text}")

async def main():
    await init_db()
    print("🤖 Бот обжалований запущен!")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
