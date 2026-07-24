from flask import Flask, request
import asyncio
import threading
from appeal_bot import main  # Импортируем main из appeal_bot.py

app = Flask(__name__)

@app.route('/')
def home():
    return '⚖️ Бот для обжалований работает!'

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        # Здесь можно обработать данные от Telegram
        return 'OK', 200
    return 'Метод не разрешён', 405

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

if __name__ == '__main__':
    thread = threading.Thread(target=run_bot)
    thread.start()
    app.run(host='0.0.0.0', port=8080)
