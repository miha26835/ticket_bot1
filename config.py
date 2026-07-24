import os

MAIN_BOT_TOKEN = os.getenv("MAIN_BOT_TOKEN")
APPEAL_BOT_TOKEN = os.getenv("APPEAL_BOT_TOKEN")
MODERATION_CHAT_ID = int(os.getenv("MODERATION_CHAT_ID"))
MODERATORS = list(map(int, os.getenv("MODERATORS").split(",")))
