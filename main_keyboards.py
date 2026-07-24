from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_moderation_keyboard(ticket_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{ticket_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{ticket_id}")
        ]
    ])
