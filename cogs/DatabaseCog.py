import sqlite3

class DatabaseCog:
    def __init__(self):
        # SQLite Database Initialization
        self.conn = sqlite3.connect('ssa.db')
        self.cursor = self.conn.cursor()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()

        create_template_table_query = """
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            TEMPLATE TEXT NOT NULL,
            DESCRIPTION TEXT,
            TITLE TEXT
        );
        """
        self.cursor.execute(create_template_table_query)
        self.conn.commit()

        create_voices_table_query = """
        CREATE TABLE IF NOT EXISTS voices (
            name TEXT PRIMARY KEY,
            voice_id TEXT NOT NULL
        );
        """
        self.cursor.execute(create_voices_table_query)
        self.conn.commit()


    def fetch_recent_messages(self, channel_id, limit=20):
        self.cursor.execute(
            "SELECT message, user_id FROM chat_history WHERE channel_id = ? ORDER BY timestamp DESC LIMIT ?",
            (channel_id, limit)
        )
        return [msg[0] for msg in reversed(self.cursor.fetchall())]

    def get_template(self, personality):
        self.cursor.execute("SELECT TEMPLATE FROM templates WHERE TITLE = ?", (personality,))
        template = self.cursor.fetchone()
        if template:
            return template[0]
        else:
            return " You are a helpful assistant."

    def insert_chat_history(self, channel_id, user_id, message, mp3_path=None, mp3_data=None):
        self.cursor.execute("""
                INSERT INTO chat_history (channel_id, user_id, message, mp3path, mp3)
                VALUES (?, ?, ?, ?, ?);
                """, (channel_id, user_id, message, mp3_path, mp3_data))
        self.conn.commit()

    def close(self):
        self.conn.close()


# Let's instantiate the DatabaseCog for further use
db_cog = DatabaseCog()
