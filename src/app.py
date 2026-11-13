
from flask import Flask, render_template, jsonify, request, Response
import csv
import io
import re

from storage import (
    get_all_logs,
    get_log_by_id,
    clear_all_logs
)

from indexer import build_index
from queue_manager import SQSQueueManager
from log_generator import AutomaticWorkloadGenerator
from worker_manager import DynamicWorkerManager


# --------------------------------------------------
# FLASK APPLICATION
# --------------------------------------------------

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)


# --------------------------------------------------
# GLOBAL OBJECTS
# --------------------------------------------------

sqs_manager = None
worker_manager = None
generator = None

services_started = False


# --------------------------------------------------
# BACKGROUND SERVICES
# --------------------------------------------------

def start_background_services():

    global sqs_manager
    global worker_manager
    global generator
    global services_started

    if services_started:
        return

    print("\n======================================")
    print(" STARTING DISTRIBUTED LOG SYSTEM")
    print("======================================")

    try:

        # ------------------------------------------
        # 1. INITIALIZE SQS QUEUE MANAGER
        # ------------------------------------------

        sqs_manager = SQSQueueManager()

        # ------------------------------------------
        # 2. INITIALIZE DYNAMIC WORKER MANAGER
        # ------------------------------------------

        worker_manager = DynamicWorkerManager(
            min_workers=2,
            max_workers=40,
            messages_per_worker=8,
            check_interval=0.75
        )

        worker_manager.start()

        # ------------------------------------------
        # 3. INITIALIZE AUTOMATIC LOG GENERATOR
        # ------------------------------------------

        generator = AutomaticWorkloadGenerator()

        # ------------------------------------------
        # 4. PUBLISH GENERATED LOGS TO SQS
        # ------------------------------------------

        def publish_log(log):

            try:
                sqs_manager.send_log(log)

            except Exception as error:

                print("[PUBLISH ERROR]", error)

                raise

        # ------------------------------------------
        # 5. START CONTINUOUS WORKLOAD
        # ------------------------------------------

        generator.start(publish_log)

        services_started = True

        print("\n[SYSTEM] All background services started.")
        print("[SYSTEM] Automatic workload is running.")
        print("[SYSTEM] Dynamic workers are monitoring SQS.")
        print("[SYSTEM] Maximum workers: 40")

    except Exception as error:

        print("[SYSTEM START ERROR]", error)

        # Clean up partially started services.
        if generator is not None:
            generator.stop()

        if worker_manager is not None:
            worker_manager.stop()

        if sqs_manager is not None:
            sqs_manager.stop()

        sqs_manager = None
        worker_manager = None
        generator = None

        raise


# --------------------------------------------------
# STOP BACKGROUND SERVICES
# --------------------------------------------------

def stop_background_services():

    global services_started

    print("\n[SYSTEM] Stopping background services...")

    # Stop new log generation first.
    if generator is not None:
        generator.stop()

    # Flush locally buffered messages to SQS.
    if sqs_manager is not None:
        sqs_manager.stop()

    # Stop the workers.
    if worker_manager is not None:
        worker_manager.stop()

    services_started = False

    print("[SYSTEM] All background services stopped.")


# --------------------------------------------------
# LOG FORMAT
# --------------------------------------------------

def log_to_dict(log):

    return {
        "id": log[0],
        "timestamp": log[1],
        "server": log[2],
        "level": log[3],
        "message": log[4]
    }


# --------------------------------------------------
# KEYWORD SEARCH HELPERS
# --------------------------------------------------

SEARCH_ALIASES = {

    "db": ["database"],
    "auth": ["authentication"],
    "signin": ["login", "logged in"],
    "signout": ["logout", "logged out"],
    "cpu": ["processor"],
    "ram": ["memory"],
    "disk": ["storage"],
    "upload": ["uploaded", "uploading"],
    "download": ["downloaded", "downloading"],
    "fail": ["failed", "failure"],
    "error": ["failed", "failure"],
    "slow": ["delayed", "slow"],
    "response": ["response time"],
    "pay": ["payment"],
    "api": ["request"]
}


def matches_keyword(log, keyword):

    if not keyword:
        return True

    searchable_text = " ".join([
        str(log[2] or ""),
        str(log[3] or ""),
        str(log[4] or "")
    ]).lower()

    words = re.findall(r"[a-z0-9]+", keyword.lower())

    for word in words:

        alternatives = [word]
        alternatives.extend(SEARCH_ALIASES.get(word, []))

        if not any(
            alternative.lower() in searchable_text
            for alternative in alternatives
        ):
            return False

    return True


# --------------------------------------------------
# SEARCH AND FILTER
# --------------------------------------------------

def get_filtered_logs():

    keyword = request.args.get(
        "keyword", ""
    ).strip()

    level = request.args.get(
        "level", ""
    ).strip().upper()

    server = request.args.get(
        "server", ""
    ).strip().upper()

    if level in ("ALL", "ALL LEVELS", "NONE"):
        level = ""

    if server in ("ALL", "ALL SERVERS", "NONE"):
        server = ""

    valid_levels = {
        "INFO",
        "WARNING",
        "ERROR"
    }

    valid_servers = {
        "SERVER-1",
        "SERVER-2",
        "SERVER-3"
    }

    if level and level not in valid_levels:
        return []

    if server and server not in valid_servers:
        return []

    logs = get_all_logs()

    filtered_logs = []

    for log in logs:

        log_level = str(log[3] or "").upper()
        log_server = str(log[2] or "").upper()

        if level and log_level != level:
            continue

        if server and log_server != server:
            continue

        if not matches_keyword(log, keyword):
            continue

        filtered_logs.append(log)

    return list(reversed(filtered_logs))


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def dashboard():

    return render_template("index.html")


# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

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

        level = str(log[3] or "").upper()
        server = str(log[2] or "").upper()

        if level in severity_counts:
            severity_counts[level] += 1

        if server in server_counts:
            server_counts[server] += 1

    recent_errors = [
        log_to_dict(log)
        for log in reversed(logs)
        if str(log[3] or "").upper() == "ERROR"
    ][:5]

    return jsonify({

        "total_logs": len(logs),

        "severity_counts": severity_counts,

        "server_counts": server_counts,

        "recent_errors": recent_errors

    })


# --------------------------------------------------
# LIVE SYSTEM STATUS
# --------------------------------------------------

@app.route("/api/system")
def get_system_status():

    worker_status = {

        "running": False,
        "active_workers": 0,
        "desired_workers": 0,
        "max_workers": 40,
        "total_processed": 0,
        "total_failed": 0,
        "workers": []

    }

    queue_status = {

        "messages_waiting": 0,
        "messages_processing": 0,
        "messages_delayed": 0

    }

    workload_status = {

        "current_phase": "Starting",
        "current_rate": 0,
        "total_generated": 0,
        "total_publish_failed": 0

    }

    publisher_status = {

        "pending_local": 0,
        "total_sent": 0,
        "total_send_failed": 0

    }

    # ----------------------------------------------
    # WORKER STATUS
    # ----------------------------------------------

    if worker_manager is not None:

        try:
            worker_status = worker_manager.get_status()

        except Exception as error:
            print("[WORKER STATUS ERROR]", error)

    # ----------------------------------------------
    # SQS QUEUE STATUS
    # ----------------------------------------------

    if sqs_manager is not None:

        try:
            queue_status = sqs_manager.get_queue_metrics()

            publisher_status = (
                sqs_manager.get_publisher_status()
            )

        except Exception as error:
            print("[QUEUE METRICS ERROR]", error)

    # ----------------------------------------------
    # GENERATOR STATUS
    # ----------------------------------------------

    if generator is not None:

        try:

            metrics = generator.get_metrics()

            workload_status = {

                "current_phase": metrics.get(
                    "current_phase", "NORMAL"
                ),

                "current_rate": metrics.get(
                    "current_rate", 0
                ),

                "total_generated": metrics.get(
                    "total_generated", 0
                ),

                "total_publish_failed": metrics.get(
                    "total_publish_failed", 0
                )

            }

        except Exception as error:
            print("[WORKLOAD METRICS ERROR]", error)

    return jsonify({

        "system_running": services_started,

        "workers": worker_status,

        "queue": queue_status,

        "workload": workload_status,

        "publisher": publisher_status

    })


# --------------------------------------------------
# LOG EXPLORER
# --------------------------------------------------

@app.route("/api/logs")
def get_logs():

    logs = get_filtered_logs()

    return jsonify({

        "count": len(logs),

        "logs": [
            log_to_dict(log)
            for log in logs
        ]

    })


# --------------------------------------------------
# INDIVIDUAL LOG DETAILS
# --------------------------------------------------

@app.route("/api/log/<int:log_id>")
def get_log_details(log_id):

    log = get_log_by_id(log_id)

    if log is None:

        return jsonify({
            "error": "Log not found"
        }), 404

    return jsonify(log_to_dict(log))


# --------------------------------------------------
# CSV EXPORT
# --------------------------------------------------

@app.route("/api/export")
def export_logs():

    logs = get_filtered_logs()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Timestamp",
        "Server",
        "Severity",
        "Message"
    ])

    for log in logs:
        writer.writerow(log)

    return Response(

        output.getvalue(),

        mimetype="text/csv",

        headers={

            "Content-Disposition":
            "attachment; filename=Distributed_Logs.csv"

        }

    )


# --------------------------------------------------
# CLEAR DATABASE LOGS
# --------------------------------------------------

@app.route("/api/clear", methods=["POST"])
def clear_logs():

    clear_all_logs()

    build_index()

    return jsonify({

        "message": (
            "Stored database logs cleared. "
            "New incoming logs will continue to be processed."
        )

    })


# --------------------------------------------------
# MANUAL GENERATION DISABLED
# --------------------------------------------------

@app.route("/api/generate", methods=["POST"])
def generate_logs():

    return jsonify({

        "message": (
            "Automatic workload generation is already running."
        )

    }), 410


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    try:

        start_background_services()

        print("\n======================================")
        print(" LOGFLOW DASHBOARD")
        print("======================================")

        print("Open http://127.0.0.1:5000")
        print("Press CTRL + C to stop.")

        print("======================================\n")

        app.run(

            host="127.0.0.1",
            port=5000,

            debug=False,
            use_reloader=False,
            threaded=True

        )

    except KeyboardInterrupt:

        print("\n[APPLICATION] Stop requested.")

    finally:

        stop_background_services()