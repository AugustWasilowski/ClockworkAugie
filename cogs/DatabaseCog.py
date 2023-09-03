import sqlite3

class DatabaseCog:
    def __init__(self):
        # SQLite Database Initialization
        self.conn = sqlite3.connect('ssa.db')
        self.cursor = self.conn.cursor()

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS 
        chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            message TEXT NOT NULL,
            mp3path TEXT NOT NULL,
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

        create_track_queue_table_query = """
                CREATE TABLE IF NOT EXISTS track_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    link TEXT NOT NULL,
                    queued_by TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
        self.cursor.execute(create_track_queue_table_query)
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

    def insert_chat_history(self, channel_id, user_id, message, mp3_path=None):
        self.cursor.execute("""
                INSERT INTO chat_history (channel_id, user_id, message, mp3path)
                VALUES (?, ?, ?, ?);
                """, (channel_id, user_id, message, mp3_path))
        self.conn.commit()

    def add_to_queue(self, channel_id, title, author, link, queued_by):
        """Add a track to the track_queue and return its ID."""
        self.cursor.execute(
            'INSERT INTO track_queue (channel_id, title, author, link, queued_by) VALUES (?, ?, ?, ?, ?);',
            (channel_id, title, author, link, queued_by)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def fetch_next_track(self, channel_id):
        """Fetch the next track to be played."""
        self.cursor.execute("""
            SELECT id, title, author, link FROM track_queue
            WHERE channel_id = ? ORDER BY timestamp ASC LIMIT 1;
            """, (channel_id,))
        return self.cursor.fetchone()

    def remove_played_track(self, track_id):
        """Remove a track from the queue after it's played."""
        self.cursor.execute("DELETE FROM track_queue WHERE id = ?", (int(track_id),))
        self.conn.commit()

    def fetch_all_tracks(self, channel_id):
        """Fetch all tracks in the queue."""
        self.cursor.execute("""
            SELECT id, title, author, link FROM track_queue
            WHERE channel_id = ? ORDER BY timestamp ASC;
            """, (channel_id,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


# Let's instantiate the DatabaseCog for further use
db_cog = DatabaseCog()
