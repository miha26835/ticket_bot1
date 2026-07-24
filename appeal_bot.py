import asyncio, logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from appeal_config import BOT_TOKEN, MODERATION_CHAT_ID, MODERATORS
from appeal_db import init_db, save_appeal, update_appeal_status, get_appeal
from appeal_keyboards import get_appeal_keyboard

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class AppealStates(StatesGroup):
    waiting_for_nick = State()
    waiting_for_reason = State()

@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "⚖️ <b>Обжалование решений</b>\n\n"
        "1️⃣ Ваш ник\n2️⃣ Причина обжалования\n\n"
        "⏱️ Ответ: 3-12 часов\n\nНапишите ваш ник:",
        parse_mode="HTML"
    )
    await state.set_state(AppealStates.waiting_for_nick)

@dp.message(AppealStates.waiting_for_nick)
async def get_nick(message: types.Message, state: FSMContext):
    await state.update_data(nick=message.text.strip())
    await message.answer("📝 Напишите причину обжалования:", parse_mode="HTML")
    await state.set_state(AppealStates.waiting_for_reason)

@dp.message(AppealStates.waiting_for_reason)
async def get_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
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
    await bot.send_message(
        chat_id=MODERATION_CHAT_ID,
        text=f"🔔 <b>Новая апелляция #{appeal_id}</b>\n\n{appeal_text}",
        parse_mode="HTML",
        reply_markup=get_appeal_keyboard(appeal_id)
    )
    await message.answer(
        f"✅ Апелляция #{appeal_id} принята! Ответ 3-12 часов.",
        parse_mode="HTML"
    )
    await state.clear()

@dp.callback_query(F.data.startswith("appeal_accept_") | F.data.startswith("appeal_reject_"))
async def handle_appeal(callback: types.CallbackQuery):
    if callback.from_user.id not in MODERATORS:
        await callback.answer("⛔ Нет прав!", show_alert=True)
        return
    action, _, appeal_id_str = callback.data.partition("_")
    appeal_id = int(appeal_id_str)
    appeal_info = await get_appeal(appeal_id)
    if not appeal_info:
        await callback.answer("❌ Апелляция не найдена!", show_alert=True)
        return
    user_id, _ = appeal_info
    status = "accepted" if action == "accept" else "rejected"
    await update_appeal_status(appeal_id, status)
    await callback.message.edit_reply_markup(reply_markup=None)
    status_text = "✅ ПРИНЯТА" if action == "accept" else "❌ ОТКЛОНЕНА"
    await callback.message.edit_text(
        f"{callback.message.text}\n\n<b>Статус:</b> {status_text}",
        parse_mode="HTML"
    )
    msg = "✅ Принята! Будет пересмотрено." if action == "accept" else "❌ Отклонена. Оснований нет."
    await bot.send_message(user_id, f"<b>Апелляция #{appeal_id}</b>\n{msg}", parse_mode="HTML")
    await callback.answer(f"✅ #{appeal_id} {status_text}")

async def main():
    await init_db()
    print("🤖 Бот обжалований запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
