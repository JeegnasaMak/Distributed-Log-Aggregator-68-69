
import random
from datetime import datetime

# Simulated application servers
SERVERS = ["SERVER-1", "SERVER-2", "SERVER-3"]

# Log severity levels
LOG_TYPES = ["INFO", "WARNING", "ERROR"]

# Sample log messages
MESSAGES = {
    "INFO": [
        "User logged in successfully",
        "Request processed successfully",
        "File uploaded successfully"
    ],
    "WARNING": [
        "High memory usage detected",
        "Response time is slow",
        "Disk space is running low"
    ],
    "ERROR": [
        "Database connection failed",
        "Payment processing failed",
        "Authentication error"
    ]
}


def generate_log():
    """Generate one random log entry."""

    server = random.choice(SERVERS)
    level = random.choice(LOG_TYPES)
    message = random.choice(MESSAGES[level])

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log = {
        "timestamp": timestamp,
        "server": server,
        "level": level,
        "message": message
    }

    return log


def generate_multiple_logs(count=10):
    """Generate multiple log entries."""

    logs = []

    for _ in range(count):
        logs.append(generate_log())

    return logs