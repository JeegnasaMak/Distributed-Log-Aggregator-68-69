
from flask import Flask, render_template, jsonify, request, Response
import csv
import io

from log_generator import generate_multiple_logs
from storage import (
    initialize_database,
    get_all_logs,
    get_logs_by_ids,
    get_log_by_id,
    clear_all_logs
)
from queue_manager import process_logs
from indexer import build_index, search_keyword


app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)


def log_to_dict(log):
    return {
        "id": log[0],
        "timestamp": log[1],
        "server": log[2],
        "level": log[3],
        "message": log[4]
    }


def get_filtered_logs():
    keyword = request.args.get("keyword", "").strip()
    level = request.args.get("level", "").strip().upper()
    server = request.args.get("server", "").strip().upper()

    if keyword:
        matching_ids = search_keyword(keyword)
        logs = get_logs_by_ids(matching_ids)
    else:
        logs = get_all_logs()

    if level:
        logs = [log for log in logs if log[3] == level]

    if server:
        logs = [log for log in logs if log[2] == server]

    return list(reversed(logs))


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/stats")
def get_stats():
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
        if log[3] in severity_counts:
            severity_counts[log[3]] += 1

        if log[2] in server_counts:
            server_counts[log[2]] += 1

    recent_errors = [
        log_to_dict(log)
        for log in reversed(logs)
        if log[3] == "ERROR"
    ][:5]

    return jsonify({
        "total_logs": len(logs),
        "severity_counts": severity_counts,
        "server_counts": server_counts,
        "recent_errors": recent_errors
    })


@app.route("/api/logs")
def get_logs():
    logs = get_filtered_logs()

    return jsonify({
        "count": len(logs),
        "logs": [log_to_dict(log) for log in logs]
    })


@app.route("/api/log/<int:log_id>")
def get_log_details(log_id):
    log = get_log_by_id(log_id)

    if log is None:
        return jsonify({"error": "Log not found"}), 404

    return jsonify(log_to_dict(log))


@app.route("/api/export")
def export_logs():
    logs = get_filtered_logs()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Timestamp", "Server", "Severity", "Message"
    ])

    for log in logs:
        writer.writerow(log)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=LogPulse_Logs.csv"
        }
    )


@app.route("/api/clear", methods=["POST"])
def clear_logs():
    clear_all_logs()
    build_index()

    return jsonify({
        "message": "All logs deleted successfully!"
    })


@app.route("/api/generate", methods=["POST"])
def generate_logs():
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

    generated_logs = generate_multiple_logs(count)

    process_logs(generated_logs, worker_count=3)

    build_index()

    return jsonify({
        "message": "Logs generated successfully!",
        "generated": len(generated_logs),
        "total_logs": len(get_all_logs())
    })


if __name__ == "__main__":
    initialize_database()
    build_index()

    print("\nStarting LogPulse Dashboard...")
    print("Open http://127.0.0.1:5000 in your browser.")

    app.run(debug=True, use_reloader=False)