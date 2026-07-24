from flask import Flask, request
import asyncio
import threading
from main_bot import main as bot_main

app = Flask(__name__)

@app.route('/')
def home():
    return '🤖 Бот работает!'

@app.route('/webhook', methods=['POST'])
def webhook():
    return 'OK', 200

def run_bot():
    # Создаём новый event loop для этого потока
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Запускаем бота в этом loop
    loop.run_until_complete(bot_main())

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)
