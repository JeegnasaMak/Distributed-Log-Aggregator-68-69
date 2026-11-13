
import time

from log_generator import AutomaticWorkloadGenerator
from queue_manager import SQSQueueManager


def main():

    print("=" * 55)
    print(" DISTRIBUTED LOG AGGREGATOR AND INDEXER")
    print(" CONTINUOUS GENERATOR + AMAZON SQS")
    print("=" * 55)

    # Step 1: Connect to Amazon SQS.
    sqs_manager = SQSQueueManager()

    # Step 2: Verify the AWS connection.
    sqs_manager.test_connection()

    # Step 3: Create the automatic workload generator.
    generator = AutomaticWorkloadGenerator()

    # Step 4: Send every generated log to Amazon SQS.
    def publish_to_sqs(log):

        message_id = sqs_manager.send_log(log)

        print(
            f"[PUBLISHED] "
            f"Phase: {log['workload_phase']} | "
            f"Server: {log['server']} | "
            f"Level: {log['level']} | "
            f"SQS ID: {message_id}"
        )

    # Step 5: Start continuous generation.
    generator.start(publish_to_sqs)

    try:

        while True:
            time.sleep(1)

            metrics = generator.get_metrics()

            print(
                f"[GENERATOR STATUS] "
                f"Phase: {metrics['current_phase']} | "
                f"Rate: {metrics['current_rate']} logs/sec | "
                f"Total generated: {metrics['total_generated']}"
            )

    except KeyboardInterrupt:

        print("\nStopping generator...")

        generator.stop()

        print("Generator stopped successfully.")


if __name__ == "__main__":
    main()