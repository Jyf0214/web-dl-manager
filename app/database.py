import sqlite3
import os
import logging
import datetime
from contextlib import contextmanager
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from .config import DATABASE_URL, BASE_DIR

# Configure basic logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Database connection pool
db_pool = None
db_type = None  # 'mysql' or 'sqlite'

def init_db_pool():
    global db_pool, db_type
    if db_pool is None:
        try:
            url = urlparse(DATABASE_URL)
            if url.scheme == 'sqlite':
                # For SQLite, store the database path as the pool
                db_path = url.path.lstrip('/')
                if not db_path:
                    # Handle in-memory SQLite
                    db_path = ":memory:"
                db_pool = db_path
                db_type = 'sqlite'
                logger.info(f"Using SQLite database: {db_path}")
            else:
                # If not a sqlite scheme, fallback to default sqlite
                db_type = 'sqlite'
                db_pool = BASE_DIR.parent / 'webdl-manager.db'
                logger.info(f"Database scheme is not sqlite, falling back to SQLite database: {db_pool}")
        except Exception as e:
            logger.error(f"Error initializing database connection: {e}")
            logger.info("Falling back to SQLite database...")
            # Fallback to SQLite
            db_type = 'sqlite'
            db_pool = BASE_DIR.parent / 'webdl-manager.db'
            logger.info(f"Using SQLite database: {db_pool}")

@contextmanager
def get_db_connection():
    if db_pool is None:
        raise Exception("Database pool not initialized. Call init_db_pool() first.")
    conn = None
    try:
        conn = sqlite3.connect(db_pool)
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        yield conn
    except sqlite3.Error as err:
        logger.error(f"Error getting database connection: {err}")
        raise
    finally:
        if conn:
            conn.close()

def init_db():
    init_db_pool() # Ensure pool is initialized
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # SQLite table creation
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    hashed_password TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("Table 'users' checked/created.")

            # Create config table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_name TEXT NOT NULL UNIQUE,
                    key_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            logger.info("Table 'config' checked/created.")

            # Create logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT,
                    logger_name TEXT,
                    message TEXT,
                    pathname TEXT,
                    lineno INTEGER
                );
            """)
            logger.info("Table 'logs' checked/created.")

            conn.commit()
        except sqlite3.Error as err:
            if "already exists" in str(err):
                logger.warning(f"Table already exists: {err}")
            else:
                logger.error(f"Error creating tables: {err}")
                raise
        finally:
            cursor.close()

class ConfigManager:
    """Manages application configuration stored in database."""
    def get_config(self, key: str, default=None):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT key_value FROM config WHERE key_name = ?", (key,))
                result = cursor.fetchone()
                cursor.close()
                if result:
                    return result[0]
                return default
        except Exception as e:
            logger.error(f"Error getting config for key '{key}': {e}")
            return default

    def set_config(self, key: str, value: str):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO config (key_name, key_value) VALUES (?, ?)",
                    (key, value)
                )
                conn.commit()
                cursor.close()
                logger.info(f"Config '{key}' set to '{value}'.")
        except Exception as e:
            logger.error(f"Error setting config for key '{key}': {e}")

db_config = ConfigManager()

class User:
    def __init__(self, id: int, username: str, hashed_password: str, is_admin: bool, **kwargs):
        self.id = id
        self.username = username
        self.hashed_password = hashed_password
        self.is_admin = is_admin

    @staticmethod
    def get_user_by_username(username: str):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user_data = cursor.fetchone()
                if user_data:
                    user_data = dict(user_data)
                cursor.close()
                if user_data:
                    return User(**user_data)
                return None
        except Exception as e:
            logger.error(f"Error getting user by username '{username}': {e}")
            return None

    @staticmethod
    def create_user(username: str, hashed_password: str, is_admin: bool = False):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, hashed_password, is_admin) VALUES (?, ?, ?)",
                    (username, hashed_password, is_admin)
                )
                conn.commit()
                cursor.close()
                logger.info(f"User '{username}' created successfully.")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Attempted to create duplicate user: '{username}'.")
            return False
        except Exception as e:
            logger.error(f"Error creating user '{username}': {e}")
            return False

    @staticmethod
    def get_first_admin_user():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE is_admin = 1 LIMIT 1")
                user_data = cursor.fetchone()
                if user_data:
                    user_data = dict(user_data)
                cursor.close()
                if user_data:
                    return User(**user_data)
                return None
        except Exception as e:
            logger.error(f"Error getting first admin user: {e}")
            return None

    @staticmethod
    def count_users():
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                cursor.close()
                return count
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0

    @staticmethod
    def update_password(username: str, new_hashed_password: str):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET hashed_password = ? WHERE username = ?",
                    (new_hashed_password, username)
                )
                conn.commit()
                cursor.close()
                logger.info(f"Password updated for user '{username}'.")
                return True
        except Exception as e:
            logger.error(f"Error updating password for user '{username}': {e}")
            return False
