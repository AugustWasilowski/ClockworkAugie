import sqlite3
from typing import List, Tuple, Dict


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
            mp3path TEXT,
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
                    id INTEGER PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    link TEXT NOT NULL,
                    queued_by TEXT NOT NULL,
                    playing BOOLEAN DEFAULT FALSE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
        self.cursor.execute(create_track_queue_table_query)
        self.conn.commit()

        create_favorite_table_query = """
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                link TEXT NOT NULL,
                queued_by INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """
        self.cursor.execute(create_favorite_table_query)
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
        print(f"Add {title} to the track_queue.")
        self.cursor.execute("""
            INSERT INTO track_queue (channel_id, title, author, link, queued_by, playing)
            VALUES (?, ?, ?, ?, ?, FALSE);
            """, (channel_id, title, author, link, queued_by))
        self.conn.commit()
        return self.cursor.lastrowid  # Return the ID of the inserted track

    def add_tracks_to_queue(self, channel_id, tracks, queued_by):
        """Add multiple tracks to the track_queue."""
        self.cursor.executemany("""
            INSERT INTO track_queue (channel_id, title, author, link, queued_by)
            VALUES (?, ?, ?, ?, ?);
            """, [(channel_id, title, author, link, queued_by) for title, author, link in tracks])
        self.conn.commit()

    def fetch_next_track(self, channel_id):
        """Fetch the next track to be played."""
        self.cursor.execute("""
            SELECT id, title, author, link FROM track_queue
            WHERE channel_id = ? AND playing = 0 ORDER BY timestamp ASC LIMIT 1;
            """, (channel_id,))
        return self.cursor.fetchone()

    def remove_played_track(self, track_id):
        print(f"Remove track {track_id} from the queue after it's played.")
        self.cursor.execute("DELETE FROM track_queue WHERE id = ?", (int(track_id),))
        self.conn.commit()

    def fetch_all_tracks(self, channel_id):
        """Fetch all tracks in the queue."""
        self.cursor.execute("""
            SELECT id, title, author, link FROM track_queue
            WHERE channel_id = ? ORDER BY timestamp ASC;
            """, (channel_id,))
        return self.cursor.fetchall()

    def fetch_track_by_id(self, track_id):
        self.cursor.execute("""
            SELECT title, author, link FROM track_queue
            WHERE id = ? ORDER BY timestamp ASC LIMIT 1;
        """, (track_id,))
        return self.cursor.fetchone()

    def set_track_playing(self, track_id):
        print(f"Set track {track_id} as currently playing.")
        self.cursor.execute("UPDATE track_queue SET playing = TRUE WHERE id = ?", (track_id,))
        self.conn.commit()

    def reset_track_playing(self, track_id):
        print(f"Reset the playing status of track {track_id}")
        self.cursor.execute("UPDATE track_queue SET playing = FALSE WHERE id = ?", (track_id,))
        self.conn.commit()

    def get_currently_playing(self, channel_id):
        print(f"Retrieve the currently playing track for channel {channel_id}")
        self.cursor.execute("SELECT id, title, author, link, queued_by FROM track_queue WHERE channel_id = ? AND "
                            "playing = TRUE",
                            (channel_id,))
        return self.cursor.fetchone()

    def reset_all_playing(self, channel_id):
        print(f"Reset the playing status for all tracks in channel {channel_id}")
        self.cursor.execute("UPDATE track_queue SET playing = FALSE WHERE channel_id = ?", (channel_id,))
        self.conn.commit()

    def clear_queue_for_channel(self):
        print(f"Clearing the playlist queue.")
        query = """
        DELETE FROM track_queue
        """
        self.cursor.execute(query, ())
        self.conn.commit()

    def check_favorite(self, link: str, user_id: int) -> bool:
        print(f"Check if the song is already in the user's favorites.")
        self.cursor.execute("""
            SELECT 1 FROM favorites WHERE link = ? AND queued_by = ?
        """, (link, user_id))
        return bool(self.cursor.fetchone())

    def add_to_favorites(self, title: str, author: str, link: str, user_id: int) -> None:
        print(f"Add {title} to the {user_id}'s favorites.")
        self.cursor.execute("""
            INSERT INTO favorites (title, author, link, queued_by)
            VALUES (?, ?, ?, ?)
        """, (title, author, link, user_id))
        self.conn.commit()

    def get_favorites(self, user_id: int) -> List[Tuple[str, str, str]]:
        print(f"Retrieve all the favorite tracks of a user, {user_id}.")
        self.cursor.execute("""
            SELECT title, author, link FROM favorites WHERE queued_by = ?
        """, (user_id,))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()


db_cog = DatabaseCog()
