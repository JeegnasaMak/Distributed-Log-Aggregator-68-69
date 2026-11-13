
from datetime import datetime
import uuid

from queue_manager import SQSQueueManager


def main():
    sqs = SQSQueueManager()

    # 1. Verify AWS connection.
    sqs.test_connection()

    # 2. Create one test log.
    test_id = str(uuid.uuid4())

    test_log = {
        "log_id": test_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "server": "SERVER-1",
        "level": "INFO",
        "message": "Testing Amazon SQS connection",
        "workload_phase": "TEST"
    }

    # 3. Send the test log to SQS.
    sqs.send_log(test_log)

    # 4. Try receiving the test message.
    print("\nWaiting to receive the test message...")

    for attempt in range(3):
        messages = sqs.receive_messages(
            max_messages=10,
            wait_time_seconds=5
        )

        for message in messages:
            if message["log"].get("log_id") == test_id:
                print("\n[TEST SUCCESSFUL]")
                print("Received test log:", message["log"])

                # 5. Delete only our own test message.
                sqs.delete_message(message["receipt_handle"])
                print("\nTest message processed and deleted.")
                return

        print(f"Attempt {attempt + 1}: Test message not received yet.")

    print("\nTest message was not found.")
    print("Check the queue in AWS Console.")


if __name__ == "__main__":
    main()