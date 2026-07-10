import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Dynamic path tracking
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, ".database", "onyx_database.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    with get_db_connection() as conn:
        # Users Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)
        
        # Chats (Sessions) Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        # Messages Table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                sender TEXT NOT NULL, -- 'user' or 'bot'
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
            )
        """)
        conn.commit()

# --- User Auth Functions ---
def register_user(username, password):
    try:
        with get_db_connection() as conn:
            hashed = generate_password_hash(password)
            conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False  # Username already taken

def check_login(username, password):
    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            return user
    return None

# --- Chat Management Functions ---
def create_new_chat(user_id, title="New Chat"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chats (user_id, title) VALUES (?, ?)", (user_id, title))
        conn.commit()
        return cursor.lastrowid

def get_user_chats(user_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()

def get_chat_messages(chat_id):
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp ASC", (chat_id,)).fetchall()

def add_message(chat_id, sender, content):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO messages (chat_id, sender, content) VALUES (?, ?, ?)", (chat_id, sender, content))
        conn.commit()

def update_chat_title(chat_id, title):
    with get_db_connection() as conn:
        conn.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))
        conn.commit()