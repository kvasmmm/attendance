import aiosqlite
from logger import logger

DB_NAME = "attendance.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                mode TEXT,
                pin TEXT,
                start_time DATETIME,
                end_time DATETIME,
                is_active BOOLEAN
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                student_id TEXT,
                ip_address TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                manual_entry BOOLEAN DEFAULT 0
            )
        """)
        await db.commit()
    logger.info("Database initialized with WAL mode.")

async def get_db():
    db = await aiosqlite.connect(DB_NAME)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()