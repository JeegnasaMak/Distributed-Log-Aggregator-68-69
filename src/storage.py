
import sqlite3
import uuid
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "logs.db"


def get_connection():
    """Create a separate SQLite connection for each operation."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.execute("PRAGMA busy_timeout = 30000")

    return connection


def initialize_database():
    """Create the logs table and safely migrate older databases."""

    connection = get_connection()

    try:
        connection.execute("PRAGMA journal_mode = WAL")

        connection.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                server TEXT,
                level TEXT,
                message TEXT,
                log_id TEXT UNIQUE
            )
        """)

        # Check whether an older database needs migration.
        columns = [
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(logs)"
            ).fetchall()
        ]

        if "log_id" not in columns:
            connection.execute(
                "ALTER TABLE logs ADD COLUMN log_id TEXT"
            )

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_logs_log_id
            ON logs(log_id)
            WHERE log_id IS NOT NULL
        """)

        connection.commit()

        print("[DATABASE] SQLite database initialized.")

    finally:
        connection.close()


def save_log(log):
    """
    Save a log only once using its unique log_id.

    Returns the database ID of the saved or existing log.
    """

    log_id = log.get("log_id")

    if not log_id:
        log_id = str(uuid.uuid4())

    connection = get_connection()

    try:
        connection.execute("""
            INSERT OR IGNORE INTO logs
            (timestamp, server, level, message, log_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            log.get("timestamp"),
            log.get("server"),
            log.get("level"),
            log.get("message"),
            log_id
        ))

        connection.commit()

        cursor = connection.execute(
            "SELECT id FROM logs WHERE log_id = ?",
            (log_id,)
        )

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"Could not find saved log: {log_id}"
            )

        return result[0]

    finally:
        connection.close()


def get_all_logs():
    connection = get_connection()

    try:
        cursor = connection.execute(
            "SELECT id, timestamp, server, level, message "
            "FROM logs ORDER BY id"
        )

        return cursor.fetchall()

    finally:
        connection.close()


def get_logs_by_ids(log_ids):
    if not log_ids:
        return []

    connection = get_connection()

    try:
        placeholders = ",".join("?" for _ in log_ids)

        query = (
            "SELECT id, timestamp, server, level, message "
            f"FROM logs WHERE id IN ({placeholders}) ORDER BY id"
        )

        cursor = connection.execute(query, tuple(log_ids))

        return cursor.fetchall()

    finally:
        connection.close()


def get_logs_by_filter(level=None, server=None):
    connection = get_connection()

    try:
        query = (
            "SELECT id, timestamp, server, level, message "
            "FROM logs WHERE 1=1"
        )

        values = []

        if level:
            query += " AND level = ?"
            values.append(level.upper())

        if server:
            query += " AND server = ?"
            values.append(server.upper())

        query += " ORDER BY id"

        cursor = connection.execute(query, values)

        return cursor.fetchall()

    finally:
        connection.close()


def get_log_by_id(log_id):
    connection = get_connection()

    try:
        cursor = connection.execute(
            "SELECT id, timestamp, server, level, message "
            "FROM logs WHERE id = ?",
            (log_id,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


def clear_all_logs():
    connection = get_connection()

    try:
        connection.execute("DELETE FROM logs")
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = 'logs'"
        )

        connection.commit()

    finally:
        connection.close()

    print("[DATABASE] All logs cleared.")