
import math
import threading
import time

from queue_manager import SQSQueueManager
from storage import save_log, initialize_database
from indexer import build_index, add_log_to_index


class DynamicWorkerManager:

    def __init__(
        self,
        min_workers=2,
        max_workers=40,
        messages_per_worker=8,
        check_interval=0.75
    ):
        self.sqs_manager = SQSQueueManager()

        self.min_workers = min_workers
        self.max_workers = max_workers
        self.messages_per_worker = messages_per_worker
        self.check_interval = check_interval

        self.workers = {}
        self.next_worker_id = 1

        self.manager_thread = None
        self.manager_stop_event = threading.Event()
        self.stats_lock = threading.Lock()

        self.total_processed = 0
        self.total_failed = 0
        self.running = False

    def start(self):
        if self.running:
            return

        initialize_database()
        build_index()
        self.sqs_manager.test_connection()

        self.manager_stop_event.clear()
        self.running = True

        self._add_workers(self.min_workers)

        self.manager_thread = threading.Thread(
            target=self._manager_loop,
            name="DynamicWorkerSupervisor",
            daemon=True
        )
        self.manager_thread.start()

        print("[MANAGER] Dynamic worker manager started.")

    def _manager_loop(self):
        while not self.manager_stop_event.is_set():
            try:
                self._remove_finished_workers()
                metrics = self.sqs_manager.get_queue_metrics()

                waiting = metrics["messages_waiting"]
                processing = metrics["messages_processing"]
                backlog = waiting + processing

                desired = math.ceil(
                    backlog / self.messages_per_worker
                )

                desired = max(self.min_workers, desired)
                desired = min(self.max_workers, desired)

                current = sum(
                    1 for worker in self.workers.values()
                    if worker["thread"].is_alive()
                    and not worker["stop_event"].is_set()
                )

                print(
                    f"[SCALING] Waiting={waiting} | "
                    f"In-flight={processing} | "
                    f"Backlog={backlog} | "
                    f"Active={current} | "
                    f"Target={desired}"
                )

                if desired > current:
                    self._add_workers(desired - current)

                elif desired < current:
                    self._remove_workers(current - desired)

            except Exception as error:
                print("[MANAGER ERROR]", error)

            self.manager_stop_event.wait(self.check_interval)

        print("[MANAGER] Supervisor stopped.")

    def _add_workers(self, count):
        for _ in range(count):
            if self.manager_stop_event.is_set():
                break

            active = sum(
                1 for worker in self.workers.values()
                if worker["thread"].is_alive()
                and not worker["stop_event"].is_set()
            )

            if active >= self.max_workers:
                break

            worker_id = self.next_worker_id
            self.next_worker_id += 1

            stop_event = threading.Event()

            worker_info = {
                "thread": None,
                "stop_event": stop_event,
                "state": "starting",
                "processed": 0,
                "failed": 0
            }

            thread = threading.Thread(
                target=self._worker_loop,
                args=(worker_id, worker_info),
                name=f"LogWorker-{worker_id}",
                daemon=True
            )

            worker_info["thread"] = thread
            self.workers[worker_id] = worker_info

            thread.start()
            print(f"[SCALING UP] Worker {worker_id} started.")

    def _remove_workers(self, count):
        candidates = sorted(
            self.workers.items(),
            key=lambda item: item[0],
            reverse=True
        )

        stopped = 0

        for worker_id, worker in candidates:
            if stopped >= count:
                break

            if (
                worker["thread"].is_alive()
                and not worker["stop_event"].is_set()
            ):
                worker["stop_event"].set()
                stopped += 1
                print(f"[SCALING DOWN] Worker {worker_id} stopping.")

    def _remove_finished_workers(self):
        finished = [
            worker_id
            for worker_id, worker in self.workers.items()
            if not worker["thread"].is_alive()
        ]

        for worker_id in finished:
            del self.workers[worker_id]
            print(f"[MANAGER] Worker {worker_id} removed.")

    def _worker_loop(self, worker_id, worker_info):
        stop_event = worker_info["stop_event"]

        print(f"[WORKER {worker_id}] Started.")

        while not stop_event.is_set():
            try:
                worker_info["state"] = "idle"

                messages = self.sqs_manager.receive_messages(
                    max_messages=10,
                    wait_time_seconds=2
                )

                if not messages:
                    continue

                for message in messages:
                    log = message["log"]
                    receipt_handle = message["receipt_handle"]

                    worker_info["state"] = "processing"

                    try:
                        database_id = save_log(log)

                        add_log_to_index(
                            database_id,
                            log.get("server", ""),
                            log.get("level", ""),
                            log.get("message", "")
                        )

                        self.sqs_manager.delete_message(receipt_handle)

                        with self.stats_lock:
                            self.total_processed += 1

                        worker_info["processed"] += 1

                    except Exception as error:
                        with self.stats_lock:
                            self.total_failed += 1

                        worker_info["failed"] += 1

                        print(
                            f"[WORKER {worker_id}] "
                            f"Processing failed: {error}"
                        )

                worker_info["state"] = "idle"

            except Exception as error:
                worker_info["state"] = "error"
                print(f"[WORKER {worker_id}] Receive error: {error}")
                time.sleep(1)

        worker_info["state"] = "stopped"
        print(f"[WORKER {worker_id}] Stopped.")

    def get_status(self):
        with self.stats_lock:
            processed = self.total_processed
            failed = self.total_failed

        worker_details = []

        for worker_id, worker in self.workers.items():
            thread = worker["thread"]

            if thread.is_alive():
                worker_details.append({
                    "id": worker_id,
                    "name": thread.name,
                    "state": worker["state"],
                    "processed": worker["processed"],
                    "failed": worker["failed"]
                })

        active = len(worker_details)

        return {
            "running": self.running,
            "active_workers": active,
            "desired_workers": active,
            "max_workers": self.max_workers,
            "total_processed": processed,
            "total_failed": failed,
            "workers": worker_details
        }

    def stop(self):
        if not self.running:
            return

        print("[MANAGER] Stopping workers...")
        self.manager_stop_event.set()

        for worker in self.workers.values():
            worker["stop_event"].set()

        if self.manager_thread:
            self.manager_thread.join(timeout=5)

        for worker in self.workers.values():
            worker["thread"].join(timeout=5)

        self._remove_finished_workers()
        self.running = False

        print("[MANAGER] Worker manager stopped.")
        print("[MANAGER] Final statistics:", self.get_status())


if __name__ == "__main__":
    manager = DynamicWorkerManager()

    try:
        manager.start()
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping requested.")

    finally:
        manager.stop()