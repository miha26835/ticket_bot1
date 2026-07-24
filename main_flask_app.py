from flask import Flask, request
import asyncio
import threading
from main_bot import main as bot_main

app = Flask(__name__)

@app.route('/')
def home():
    return '🤖 Бот работает!'

# Обработчик для вебхука (пока заглушка)
@app.route('/webhook', methods=['POST'])
def webhook():
    return 'OK', 200

def run_bot():
    bot_main()  # Это твоя функция main() из main_bot.py

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)
