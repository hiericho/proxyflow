from contextlib import asynccontextmanager
import aiosqlite
import os

DB_PATH = "proxies.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                protocol TEXT,
                latency REAL,
                status TEXT DEFAULT 'unknown',
                last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

@asynccontextmanager
async def get_db_session():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
