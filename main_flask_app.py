from flask import Flask, request
from main_bot import bot, dp, main
import asyncio, threading

app = Flask(__name__)

@app.route('/')
def home():
    return 'Тикет-бот запущен!'

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = request.get_json()
    await dp.process_update(update)
    return 'OK', 200

def run_bot():
    asyncio.run(main())

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run()
