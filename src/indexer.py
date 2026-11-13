
import re
import threading

from storage import get_all_logs


# Stores each keyword and the IDs of logs containing it.
inverted_index = {}

# Prevents multiple workers from modifying the index simultaneously.
index_lock = threading.Lock()


def extract_keywords(text):
    """Convert text into searchable lowercase keywords."""

    return re.findall(
        r"\b[a-zA-Z0-9-]+\b",
        text.lower()
    )


def add_log_to_index(log_id, server, level, message):
    """
    Add only one newly processed log to the existing index.
    This avoids rebuilding the complete index after every log.
    """

    text = f"{server} {level} {message}"

    words = extract_keywords(text)

    with index_lock:

        for word in words:

            if word not in inverted_index:
                inverted_index[word] = set()

            inverted_index[word].add(log_id)


def build_index():
    """
    Build the complete inverted index from SQLite.
    Called once when the application starts.
    """

    global inverted_index

    logs = get_all_logs()

    new_index = {}

    for log in logs:

        log_id = log[0]
        server = log[2]
        level = log[3]
        message = log[4]

        text = f"{server} {level} {message}"

        words = extract_keywords(text)

        for word in words:

            if word not in new_index:
                new_index[word] = set()

            new_index[word].add(log_id)

    with index_lock:
        inverted_index = new_index

    print("\n[INDEX] Inverted index built successfully!")
    print(f"[INDEX] Total indexed keywords: {len(inverted_index)}")
    print(f"[INDEX] Total logs indexed: {len(logs)}")


def search_keyword(keyword):
    """Find log IDs containing a particular keyword."""

    keyword = keyword.lower().strip()

    if not keyword:
        return []

    with index_lock:
        log_ids = inverted_index.get(keyword, set())

        return sorted(log_ids)