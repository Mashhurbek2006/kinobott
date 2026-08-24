import sqlite3

DB_NAME = "movies.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            code TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            name TEXT,
            lang TEXT,
            quality TEXT,
            message_id INTEGER,
            channel_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            chat_id TEXT PRIMARY KEY,
            name TEXT,
            url TEXT,
            style TEXT,
            emoji_id TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_movies (
            user_id INTEGER,
            code TEXT,
            PRIMARY KEY (user_id, code)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    # Ensure join_requests table exists for subscription tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS join_requests (
            user_id INTEGER,
            chat_id TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')

    conn.close()

def add_channel(chat_id, name, url, style, emoji_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO channels (chat_id, name, url, style, emoji_id) VALUES (?, ?, ?, ?, ?)', (str(chat_id), name, url, style, emoji_id))
    conn.commit()
    conn.close()

def remove_channel(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM channels WHERE chat_id = ?', (str(chat_id),))
    conn.commit()
    conn.close()

def get_channels():
    """Return list of all mandatory channels."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, name, url, style, emoji_id FROM channels')
    rows = cursor.fetchall()
    conn.close()
    return [
        {"chat_id": row[0], "name": row[1], "url": row[2], "style": row[3], "emoji_id": row[4]}
        for row in rows
    ]


def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_new_user_count(days):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE created_at >= datetime("now", "-" || ? || " days")', (days,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_user_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_user_ids():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_movie_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM movies')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_movies():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT code, name, lang, quality FROM movies ORDER BY rowid DESC')
    rows = cursor.fetchall()
    conn.close()
    return [{"code": r[0], "name": r[1], "lang": r[2], "quality": r[3]} for r in rows]

def delete_movie(code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM movies WHERE code = ?', (code,))
    conn.commit()
    conn.close()

def add_join_request(user_id, chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO join_requests (user_id, chat_id) VALUES (?, ?)', (user_id, str(chat_id)))
    conn.commit()
    conn.close()

def has_join_request(user_id, chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM join_requests WHERE user_id = ? AND chat_id = ?', (user_id, str(chat_id)))
    result = cursor.fetchone()
    conn.close()
    return bool(result)

def add_movie(code, file_id, name, lang, quality, message_id=None, channel_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO movies (code, file_id, name, lang, quality, message_id, channel_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (code, file_id, name, lang, quality, message_id, channel_id))
    conn.commit()
    conn.close()

def get_movie(code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT file_id, name, lang, quality FROM movies WHERE code = ?', (code,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "file_id": result[0],
            "name": result[1],
            "lang": result[2],
            "quality": result[3]
        }
    return None

def set_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else default

def delete_setting(key):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM settings WHERE key = ?', (key,))
    conn.commit()
    conn.close()

def get_total_saved_movies_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM saved_movies')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def save_movie(user_id, code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO saved_movies (user_id, code) VALUES (?, ?)', (user_id, code))
    conn.commit()
    conn.close()

def remove_saved_movie(user_id, code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM saved_movies WHERE user_id = ? AND code = ?', (user_id, code))
    conn.commit()
    conn.close()

def get_saved_movies(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.code, m.name, m.lang, m.quality, m.file_id
        FROM saved_movies s
        JOIN movies m ON s.code = m.code
        WHERE s.user_id = ?
    ''', (user_id,))
    result = cursor.fetchall()
    conn.close()
    return [{"code": r[0], "name": r[1], "lang": r[2], "quality": r[3], "file_id": r[4]} for r in result]

def export_all_data():
    """Barcha ma'lumotlarni JSON formatida eksport qilish (backup uchun)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT code, file_id, name, lang, quality, message_id, channel_id FROM movies')
    movies = [{"code": r[0], "file_id": r[1], "name": r[2], "lang": r[3], "quality": r[4], "message_id": r[5], "channel_id": r[6]} for r in cursor.fetchall()]

    cursor.execute('SELECT chat_id, name, url, style, emoji_id FROM channels')
    channels = [{"chat_id": r[0], "name": r[1], "url": r[2], "style": r[3], "emoji_id": r[4]} for r in cursor.fetchall()]

    cursor.execute('SELECT key, value FROM settings')
    settings = {r[0]: r[1] for r in cursor.fetchall()}

    cursor.execute('SELECT user_id FROM users')
    users = [r[0] for r in cursor.fetchall()]

    conn.close()
    return {"movies": movies, "channels": channels, "settings": settings, "users": users}

def import_all_data(data):
    """JSON ma'lumotlardan bazani tiklash (restore)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for m in data.get("movies", []):
        cursor.execute('INSERT OR REPLACE INTO movies (code, file_id, name, lang, quality, message_id, channel_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (m["code"], m["file_id"], m["name"], m["lang"], m["quality"], m.get("message_id"), m.get("channel_id")))

    for ch in data.get("channels", []):
        cursor.execute('INSERT OR REPLACE INTO channels (chat_id, name, url, style, emoji_id) VALUES (?, ?, ?, ?, ?)',
            (ch["chat_id"], ch["name"], ch["url"], ch["style"], ch.get("emoji_id", "")))

    for key, value in data.get("settings", {}).items():
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))

    for uid in data.get("users", []):
        cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (uid,))

    conn.commit()
    conn.close()
