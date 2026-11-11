
import queue
import threading

from storage import save_log

# Create a central queue
log_queue = queue.Queue()


def worker(worker_id):
    """Worker takes logs from queue and saves them."""

    while True:

        log = log_queue.get()

        try:
            # None is the signal to stop a worker
            if log is None:
                break

            print(f"Worker {worker_id} processing: {log['level']} - {log['message']}")

            # Save processed log into database
            save_log(log)

            print(f"Worker {worker_id} completed log!")

        finally:
            log_queue.task_done()


def process_logs(logs, worker_count=3):
    """Start workers and distribute logs through the queue."""

    workers = []

    print("\nStarting log processing workers...")

    # Create and start multiple workers
    for i in range(worker_count):

        thread = threading.Thread(
            target=worker,
            args=(i + 1,)
        )

        thread.start()
        workers.append(thread)

    print(f"{worker_count} workers started successfully!")

    # Add all generated logs to the queue
    for log in logs:
        log_queue.put(log)

    print(f"\n{len(logs)} logs added to central queue!")

    # Wait until all logs are processed
    log_queue.join()

    # Stop all workers
    for _ in workers:
        log_queue.put(None)

    log_queue.join()

    # Wait for all workers to stop
    for thread in workers:
        thread.join()

    print("\nAll logs processed successfully!")