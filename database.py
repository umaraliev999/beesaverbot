import sqlite3
import os
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "bot_data.db")


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                joined_at   TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS downloads (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                platform    TEXT,
                media_type  TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );
        """)
        self.conn.commit()

    def add_user(self, user_id: int, username: str, full_name: str):
        self.conn.execute(
            "INSERT OR IGNORE INTO users (id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name),
        )
        self.conn.commit()

    def add_download(self, user_id: int, platform: str, media_type: str):
        self.conn.execute(
            "INSERT INTO downloads (user_id, platform, media_type) VALUES (?, ?, ?)",
            (user_id, platform, media_type),
        )
        self.conn.commit()

    def get_stats(self) -> dict:
        cur = self.conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM downloads")
        total_downloads = cur.fetchone()[0]

        platforms = ["youtube", "instagram", "tiktok", "pinterest"]
        platform_stats = {}
        for p in platforms:
            cur.execute("SELECT COUNT(*) FROM downloads WHERE platform=?", (p,))
            platform_stats[p] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM downloads WHERE media_type='audio'")
        audio = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM downloads WHERE media_type='video'")
        video = cur.fetchone()[0]

        return {
            "total_users": total_users,
            "total_downloads": total_downloads,
            **platform_stats,
            "audio": audio,
            "video": video,
        }


# Global instance
db = Database()
