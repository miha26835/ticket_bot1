import asyncio, logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from main_config import BOT_TOKEN, MODERATION_CHAT_ID, MODERATORS
from main_db import init_db, save_ticket, update_ticket_status, get_ticket
from main_keyboards import get_moderation_keyboard

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class TicketStates(StatesGroup):
    waiting_for_nick = State()
    waiting_for_violation = State()
    waiting_for_proof = State()

@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🛡️ <b>Добро пожаловать в систему тикетов!</b>\n\n"
        "1️⃣ Ник нарушителя\n2️⃣ Что он делал\n3️⃣ Запись нарушения\n\nНапиши ник:",
        parse_mode="HTML"
    )
    await state.set_state(TicketStates.waiting_for_nick)

@dp.message(TicketStates.waiting_for_nick)
async def get_nick(message: types.Message, state: FSMContext):
    await state.update_data(nick=message.text.strip())
    await message.answer("📝 Опиши нарушение:", parse_mode="HTML")
    await state.set_state(TicketStates.waiting_for_violation)

@dp.message(TicketStates.waiting_for_violation)
async def get_violation(message: types.Message, state: FSMContext):
    await state.update_data(violation=message.text.strip())
    await message.answer("📎 Пришли доказательство:", parse_mode="HTML")
    await state.set_state(TicketStates.waiting_for_proof)

@dp.message(TicketStates.waiting_for_proof)
async def get_proof(message: types.Message, state: FSMContext):
    data = await state.get_data()
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
        f"📩 <b>Отправил:</b> @{message.from_user.username or 'нет юзернейма'}"
    )
    
    ticket_id = await save_ticket(
        user_id=message.from_user.id,
        username=message.from_user.username or "без_юзера",
        ticket_text=ticket_text
    )
    
    await bot.send_message(
        chat_id=MODERATION_CHAT_ID,
        text=f"🔔 <b>Новый тикет #{ticket_id}</b>\n\n{ticket_text}",
        parse_mode="HTML",
        reply_markup=get_moderation_keyboard(ticket_id)
    )
    
    await message.answer(
        f"✅ Тикет #{ticket_id} принят! Модераторы рассмотрят.",
        parse_mode="HTML"
    )
    await state.clear()

@dp.callback_query(F.data.startswith("accept_") | F.data.startswith("reject_"))
async def handle_moderation(callback: types.CallbackQuery):
    if callback.from_user.id not in MODERATORS:
        await callback.answer("⛔ Нет прав!", show_alert=True)
        return
    action, ticket_id_str = callback.data.split("_")
    ticket_id = int(ticket_id_str)
    ticket_info = await get_ticket(ticket_id)
    if not ticket_info:
        await callback.answer("❌ Тикет не найден!", show_alert=True)
        return
    user_id, _ = ticket_info
    status = "accepted" if action == "accept" else "rejected"
    await update_ticket_status(ticket_id, status)
    await callback.message.edit_reply_markup(reply_markup=None)
    status_text = "✅ ПРИНЯТ" if action == "accept" else "❌ ОТКЛОНЁН"
    await callback.message.edit_text(
        f"{callback.message.text}\n\n<b>Статус:</b> {status_text}",
        parse_mode="HTML"
    )
    msg = "✅ Принят! Игрок получит наказание." if action == "accept" else "❌ Отклонён. Недостаточно доказательств."
    await bot.send_message(user_id, f"<b>Тикет #{ticket_id}</b>\n{msg}", parse_mode="HTML")
    await callback.answer(f"✅ #{ticket_id} {status_text}")

async def main():
    await init_db()
    print("🤖 Основной бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
