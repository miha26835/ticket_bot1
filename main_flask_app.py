from flask import Flask, request
import asyncio
from main_bot import main as bot_main

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Тикет-бот запущен!'

@app.route('/webhook', methods=['POST'])
async def webhook():
    # Для webhook нужно будет переделать, но пока оставим заглушку
    return 'OK', 200

def run_bot():
    asyncio.run(bot_main())

if __name__ == '__main__':
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)
