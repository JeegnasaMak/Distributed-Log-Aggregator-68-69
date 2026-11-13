
import random
import time
import threading
import uuid
from datetime import datetime


# --------------------------------------------------
# AVAILABLE SERVERS
# --------------------------------------------------

SERVERS = [
    "SERVER-1",
    "SERVER-2",
    "SERVER-3"
]


# --------------------------------------------------
# AVAILABLE SEVERITY LEVELS
# --------------------------------------------------

LOG_TYPES = [
    "INFO",
    "WARNING",
    "ERROR"
]


# --------------------------------------------------
# LOG MESSAGE LIBRARY
# --------------------------------------------------

MESSAGES = {

    "INFO": [
        "User logged in successfully",
        "User logout completed successfully",
        "Request processed successfully",
        "API request completed successfully",
        "File uploaded successfully",
        "File downloaded successfully",
        "Database backup completed",
        "Database connection established",
        "Payment received successfully",
        "Authentication completed successfully",
        "New user registered successfully",
        "Server started successfully",
        "Cache updated successfully",
        "Data synchronization completed",
        "Report generated successfully",
        "Email notification sent successfully",
        "Record inserted successfully",
        "Application health check passed",
        "Transaction completed successfully",
        "Configuration updated successfully"
    ],

    "WARNING": [
        "High memory usage detected",
        "Response time is slow",
        "Disk space is running low",
        "High CPU usage detected",
        "Database response delayed",
        "Network latency is high",
        "API response time exceeded threshold",
        "Cache memory usage is high",
        "Multiple login attempts detected",
        "File upload is taking longer than expected",
        "Server workload is increasing",
        "Connection pool is nearly full",
        "Storage capacity is almost exhausted",
        "Request queue is growing",
        "Background task is taking longer than expected",
        "Payment response is delayed",
        "Database query execution is slow",
        "Worker processing time is high",
        "Service response is slower than normal",
        "Retry attempt required"
    ],

    "ERROR": [
        "Database connection failed",
        "Payment processing failed",
        "Authentication error",
        "API request failed",
        "File upload failed",
        "File download failed",
        "Database query execution failed",
        "User login failed",
        "Server connection lost",
        "Network connection failed",
        "Cache update failed",
        "Email notification delivery failed",
        "Transaction processing failed",
        "Database timeout occurred",
        "Invalid user credentials",
        "Service unavailable",
        "Data synchronization failed",
        "Worker failed to process message",
        "Storage operation failed",
        "Unexpected application exception"
    ]
}


# --------------------------------------------------
# AUTOMATIC WORKLOAD PATTERN
# --------------------------------------------------

# These are target generation rates, not guaranteed
# end-to-end SQS processing rates.

WORKLOAD_PATTERN = [
    {"phase": "NORMAL", "rate": 20, "duration": 15},
    {"phase": "INCREASING", "rate": 80, "duration": 15},
    {"phase": "SPIKE", "rate": 250, "duration": 15},
    {"phase": "HEAVY", "rate": 350, "duration": 15},
    {"phase": "DECREASING", "rate": 80, "duration": 15}
]


# --------------------------------------------------
# GENERATE ONE LOG
# --------------------------------------------------

def generate_log(workload_phase="NORMAL"):

    server = random.choice(SERVERS)
    level = random.choice(LOG_TYPES)
    message = random.choice(MESSAGES[level])

    return {
        "log_id": str(uuid.uuid4()),

        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        ),

        "server": server,
        "level": level,
        "message": message,
        "workload_phase": workload_phase
    }


# --------------------------------------------------
# GENERATE MULTIPLE LOGS
# --------------------------------------------------

def generate_multiple_logs(count=10):

    return [
        generate_log()
        for _ in range(count)
    ]


# --------------------------------------------------
# AUTOMATIC WORKLOAD GENERATOR
# --------------------------------------------------

class AutomaticWorkloadGenerator:

    def __init__(self):

        self.stop_event = threading.Event()
        self.generator_thread = None

        self.current_phase = "STOPPED"
        self.current_rate = 0
        self.total_generated = 0
        self.total_publish_failed = 0

        self.metrics_lock = threading.Lock()

    # ----------------------------------------------
    # START GENERATOR
    # ----------------------------------------------

    def start(self, publish_callback):

        if (
            self.generator_thread
            and self.generator_thread.is_alive()
        ):
            print("Log generator is already running.")
            return

        self.stop_event.clear()

        self.generator_thread = threading.Thread(
            target=self._run,
            args=(publish_callback,),
            name="AutomaticLogGenerator",
            daemon=True
        )

        self.generator_thread.start()

        print("[GENERATOR] Automatic workload started.")

    # ----------------------------------------------
    # MAIN GENERATION LOOP
    # ----------------------------------------------

    def _run(self, publish_callback):

        while not self.stop_event.is_set():

            for stage in WORKLOAD_PATTERN:

                if self.stop_event.is_set():
                    break

                phase = stage["phase"]
                rate = stage["rate"]
                duration = stage["duration"]

                interval = 1.0 / rate

                with self.metrics_lock:
                    self.current_phase = phase
                    self.current_rate = rate

                print(
                    f"\n[WORKLOAD] {phase} | "
                    f"Target: {rate} logs/sec | "
                    f"Duration: {duration}s"
                )

                stage_end = time.monotonic() + duration
                next_log_time = time.monotonic()

                generated_in_phase = 0

                while (
                    not self.stop_event.is_set()
                    and time.monotonic() < stage_end
                ):

                    now = time.monotonic()

                    if now < next_log_time:

                        self.stop_event.wait(
                            min(next_log_time - now, 0.01)
                        )

                        continue

                    log = generate_log(phase)

                    try:

                        publish_callback(log)

                        with self.metrics_lock:
                            self.total_generated += 1

                        generated_in_phase += 1

                    except Exception as error:

                        with self.metrics_lock:
                            self.total_publish_failed += 1

                        print(
                            f"[GENERATOR ERROR] {error}"
                        )

                    next_log_time += interval

                    # Avoid uncontrolled catch-up bursts
                    # if the computer falls behind.

                    if next_log_time < time.monotonic() - 1:
                        next_log_time = time.monotonic()

                print(
                    f"[WORKLOAD COMPLETE] {phase} | "
                    f"Generated: {generated_in_phase}"
                )

        with self.metrics_lock:
            self.current_phase = "STOPPED"
            self.current_rate = 0

        print("\n[GENERATOR] Workload stopped.")

    # ----------------------------------------------
    # STOP GENERATOR
    # ----------------------------------------------

    def stop(self):

        self.stop_event.set()

        if self.generator_thread:
            self.generator_thread.join(timeout=10)

    # ----------------------------------------------
    # GET GENERATOR METRICS
    # ----------------------------------------------

    def get_metrics(self):

        with self.metrics_lock:

            return {
                "current_phase": self.current_phase,
                "current_rate": self.current_rate,
                "total_generated": self.total_generated,
                "total_publish_failed": self.total_publish_failed
            }


# --------------------------------------------------
# STANDALONE TESTING
# --------------------------------------------------

if __name__ == "__main__":

    generator = AutomaticWorkloadGenerator()

    def test_publish(log):

        print(
            f"[NEW LOG] "
            f"{log['server']} | "
            f"{log['level']} | "
            f"{log['message']} | "
            f"Phase: {log['workload_phase']}"
        )

    print("Starting automatic workload generation...")

    generator.start(test_publish)

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nStopping generator...")
        generator.stop()

        print("Generator stopped successfully.")