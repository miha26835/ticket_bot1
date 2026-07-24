import aiosqlite
DB_PATH = "appeals.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS appeals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                appeal_text TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        await db.commit()

async def save_appeal(user_id, username, appeal_text):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO appeals (user_id, username, appeal_text) VALUES (?, ?, ?)",
            (user_id, username, appeal_text)
        )
        await db.commit()
        return cursor.lastrowid

async def update_appeal_status(appeal_id, status):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE appeals SET status = ? WHERE id = ?",
            (status, appeal_id)
        )
        await db.commit()

async def get_appeal(appeal_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, appeal_text FROM appeals WHERE id = ?",
            (appeal_id,)
        ) as cursor:
            return await cursor.fetchone()
