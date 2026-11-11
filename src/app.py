
from flask import Flask, render_template, jsonify, request

from log_generator import generate_multiple_logs
from storage import (
    initialize_database,
    get_all_logs,
    get_logs_by_ids,
    get_logs_by_filter
)
from queue_manager import process_logs
from indexer import build_index, search_keyword


# Configure Flask paths
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)


def log_to_dict(log):
    """Convert a database log row into a dictionary."""

    return {
        "id": log[0],
        "timestamp": log[1],
        "server": log[2],
        "level": log[3],
        "message": log[4]
    }


@app.route("/")
def dashboard():
    """Display the main dashboard."""
    return render_template("index.html")


@app.route("/api/stats")
def get_stats():
    """Return dashboard statistics."""

    logs = get_all_logs()

    severity_counts = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0
    }

    server_counts = {
        "SERVER-1": 0,
        "SERVER-2": 0,
        "SERVER-3": 0
    }

    for log in logs:
        level = log[3]
        server = log[2]

        if level in severity_counts:
            severity_counts[level] += 1

        if server in server_counts:
            server_counts[server] += 1

    return jsonify({
        "total_logs": len(logs),
        "severity_counts": severity_counts,
        "server_counts": server_counts
    })


@app.route("/api/logs")
def get_logs():
    """Search and filter stored logs."""

    keyword = request.args.get("keyword", "").strip()
    level = request.args.get("level", "").strip().upper()
    server = request.args.get("server", "").strip().upper()

    # Start with all logs or keyword matches
    if keyword:
        matching_ids = search_keyword(keyword)
        logs = get_logs_by_ids(matching_ids)
    else:
        logs = get_all_logs()

    # Apply severity and server filters
    if level:
        logs = [log for log in logs if log[3] == level]

    if server:
        logs = [log for log in logs if log[2] == server]

    # Show newest logs first
    logs = list(reversed(logs))

    return jsonify({
        "count": len(logs),
        "logs": [log_to_dict(log) for log in logs]
    })


@app.route("/api/generate", methods=["POST"])
def generate_logs():
    """Generate and process new logs from the dashboard."""

    data = request.get_json(silent=True) or {}

    try:
        count = int(data.get("count", 10))

        if count <= 0 or count > 1000:
            return jsonify({
                "error": "Enter a number between 1 and 1000."
            }), 400

    except (ValueError, TypeError):
        return jsonify({
            "error": "Please enter a valid whole number."
        }), 400

    # Generate logs
    generated_logs = generate_multiple_logs(count)

    # Process logs through the worker queue
    process_logs(generated_logs, worker_count=3)

    # Refresh the inverted index
    build_index()

    return jsonify({
        "message": "Logs generated and stored successfully!",
        "generated": len(generated_logs),
        "total_logs": len(get_all_logs())
    })


if __name__ == "__main__":
    initialize_database()
    build_index()

    print("\nStarting Distributed Log Aggregator Dashboard...")
    print("Open http://127.0.0.1:5000 in your browser.")

    app.run(debug=True, use_reloader=False)