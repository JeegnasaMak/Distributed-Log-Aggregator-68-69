
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "logs.db"


def initialize_database():
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            server TEXT,
            level TEXT,
            message TEXT
        )
    """)

    connection.commit()
    connection.close()


def save_log(log):
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)

    connection.execute("""
        INSERT INTO logs (timestamp, server, level, message)
        VALUES (?, ?, ?, ?)
    """, (
        log["timestamp"],
        log["server"],
        log["level"],
        log["message"]
    ))

    connection.commit()
    connection.close()


def get_all_logs():
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute(
        "SELECT * FROM logs ORDER BY id"
    )

    logs = cursor.fetchall()
    connection.close()

    return logs


def get_logs_by_ids(log_ids):
    if not log_ids:
        return []

    connection = sqlite3.connect(DATABASE_PATH)

    placeholders = ",".join("?" for _ in log_ids)

    query = f"""
        SELECT * FROM logs
        WHERE id IN ({placeholders})
        ORDER BY id
    """

    cursor = connection.execute(query, tuple(log_ids))

    logs = cursor.fetchall()
    connection.close()

    return logs


def get_logs_by_filter(level=None, server=None):
    connection = sqlite3.connect(DATABASE_PATH)

    query = "SELECT * FROM logs WHERE 1=1"
    values = []

    if level:
        query += " AND level = ?"
        values.append(level.upper())

    if server:
        query += " AND server = ?"
        values.append(server.upper())

    query += " ORDER BY id"

    cursor = connection.execute(query, values)
    logs = cursor.fetchall()

    connection.close()
    return logs


# Get one log using its ID
def get_log_by_id(log_id):
    connection = sqlite3.connect(DATABASE_PATH)

    cursor = connection.execute(
        "SELECT * FROM logs WHERE id = ?",
        (log_id,)
    )

    log = cursor.fetchone()
    connection.close()

    return log


# Delete all stored logs
def clear_all_logs():
    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("DELETE FROM logs")

    # Reset the automatic ID counter
    connection.execute(
        "DELETE FROM sqlite_sequence WHERE name = 'logs'"
    )

    connection.commit()
    connection.close()