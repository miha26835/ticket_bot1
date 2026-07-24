from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_appeal_keyboard(appeal_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"appeal_accept_{appeal_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"appeal_reject_{appeal_id}")
        ]
    ])
