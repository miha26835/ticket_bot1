from flask import Flask, request
from main_bot import bot, dp, main
import asyncio

app = Flask(__name__)

# Это страница, которую видит пользователь при переходе на сайт бота
@app.route('/')
def home():
    return '🤖 Бот работает!'

# Это обработчик вебхука — сюда Telegram отправляет сообщения
@app.route('/webhook', methods=['POST'])
async def webhook():
    update = request.get_json()
    await dp.process_update(update)
    return 'OK', 200

# Запускает бота в фоновом потоке (чтобы не мешать веб-серверу)
def run_bot():
    asyncio.run(main())

if __name__ == '__main__':
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)  # Порт 8080 — стандартный для Render
