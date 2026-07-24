import aiosqlite
DB_PATH = "tickets.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                ticket_text TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        await db.commit()

async def save_ticket(user_id, username, ticket_text):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO tickets (user_id, username, ticket_text) VALUES (?, ?, ?)",
            (user_id, username, ticket_text)
        )
        await db.commit()
        return cursor.lastrowid

async def update_ticket_status(ticket_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET status = ? WHERE id = ?",
            (status, ticket_id)
        )
        await db.commit()

async def get_ticket(ticket_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, ticket_text FROM tickets WHERE id = ?",
            (ticket_id,)
        ) as cursor:
            return await cursor.fetchone()
