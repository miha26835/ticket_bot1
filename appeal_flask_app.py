from flask import Flask, request
from appeal_bot import bot, dp, main
import asyncio

app = Flask(__name__)

@app.route('/')
def home():
    return '⚖️ Бот для обжалований работает!'

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = request.get_json()
    await dp.process_update(update)
    return 'OK', 200

def run_bot():
    asyncio.run(main())

if __name__ == '__main__':
    import threading
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=8080)
