
import re
from storage import get_all_logs


# Store keywords and their corresponding log IDs
inverted_index = {}


def build_index():
    """Build an inverted index using all stored logs."""

    global inverted_index
    inverted_index = {}

    logs = get_all_logs()

    for log in logs:
        log_id = log[0]

        # Combine searchable log information
        text = f"{log[2]} {log[3]} {log[4]}"

        # Convert text into lowercase keywords
        words = re.findall(r"\b[a-zA-Z0-9-]+\b", text.lower())

        for word in words:
            if word not in inverted_index:
                inverted_index[word] = set()

            inverted_index[word].add(log_id)

    print("\nInverted index built successfully!")
    print(f"Total indexed keywords: {len(inverted_index)}")


def search_keyword(keyword):
    """Find log IDs containing the given keyword."""

    keyword = keyword.lower().strip()

    if not keyword:
        return []

    log_ids = inverted_index.get(keyword, set())

    return sorted(log_ids)