
import time

from log_generator import AutomaticWorkloadGenerator
from queue_manager import SQSQueueManager
from worker_manager import DynamicWorkerManager


def main():
    print("\n======================================")
    print(" DISTRIBUTED LOG AGGREGATOR & INDEXER")
    print("======================================")

    sqs_manager = SQSQueueManager()
    worker_manager = DynamicWorkerManager(
        min_workers=1,
        messages_per_worker=10,
        check_interval=5
    )
    generator = AutomaticWorkloadGenerator()

    try:
        # Step 1: Start dynamic workers
        worker_manager.start()

        # Step 2: Publish generated logs to SQS
        def publish_log(log):
            sqs_manager.send_log(log)

        # Step 3: Start continuous automatic generation
        generator.start(publish_log)

        print("\n[SYSTEM] All services are running.")
        print("[SYSTEM] Workload will change automatically.")
        print("[SYSTEM] Workers will scale according to queue backlog.")
        print("[SYSTEM] Press CTRL + C to stop.\n")

        # Step 4: Display system status continuously
        while True:
            time.sleep(5)

            worker_status = worker_manager.get_status()
            queue_status = sqs_manager.get_queue_metrics()

            print("\n========== SYSTEM STATUS ==========")
            print("Active workers:", worker_status["active_workers"])
            print("Total processed:", worker_status["total_processed"])
            print("Total failed:", worker_status["total_failed"])
            print("Messages waiting:", queue_status["messages_waiting"])
            print("Messages processing:", queue_status["messages_processing"])
            print("===================================\n")

    except KeyboardInterrupt:
        print("\n[SYSTEM] Stopping requested.")

    finally:
        print("\n[SYSTEM] Stopping log generator...")
        generator.stop()

        print("[SYSTEM] Stopping worker manager...")
        worker_manager.stop()

        print("\n[SYSTEM] All services stopped.")


if __name__ == "__main__":
    main()