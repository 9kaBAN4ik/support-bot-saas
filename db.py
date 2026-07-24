import aiosqlite
from config import DB_PATH
import os


async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                welcome_message TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                business_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (business_id, date),
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        await db.commit()


async def create_business(owner_id: int, name: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO businesses (owner_id, name) VALUES (?, ?)",
            (owner_id, name),
        )
        await db.commit()
        return cursor.lastrowid


async def get_business_by_owner(owner_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM businesses WHERE owner_id = ?", (owner_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_business(owner_id: int, **kwargs):
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [owner_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE businesses SET {fields} WHERE owner_id = ?", values
        )
        await db.commit()


async def log_message(business_id: int, user_id: int, question: str, answer: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages_log (business_id, user_id, question, answer) VALUES (?, ?, ?, ?)",
            (business_id, user_id, question, answer),
        )
        await db.commit()


async def increment_usage(business_id: int, date: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO daily_usage (business_id, date, count) VALUES (?, ?, 1)
               ON CONFLICT(business_id, date) DO UPDATE SET count = count + 1""",
            (business_id, date),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT count FROM daily_usage WHERE business_id = ? AND date = ?",
            (business_id, date),
        )
        row = await cursor.fetchone()
        return row[0]


async def get_stats(business_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM messages_log WHERE business_id = ?",
            (business_id,),
        )
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM messages_log WHERE business_id = ?",
            (business_id,),
        )
        users = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM messages_log WHERE business_id = ? AND date(created_at) = date('now')",
            (business_id,),
        )
        today = (await cursor.fetchone())[0]

        return {"total_messages": total, "unique_users": users, "today": today}
