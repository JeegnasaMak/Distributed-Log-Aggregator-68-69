
import json
import os
import threading
import time
from pathlib import Path

import boto3
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError


PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")


class SQSQueueManager:

    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.queue_url = os.getenv("SQS_QUEUE_URL")

        if not self.queue_url:
            raise ValueError("SQS_QUEUE_URL is missing from .env")

        self.sqs = boto3.client("sqs", region_name=self.region)

        # Automatic batching for the existing send_log(log) interface.
        self.batch_size = 10
        self.flush_interval = 0.15
        self.pending_logs = []
        self.pending_lock = threading.Lock()
        self.flush_event = threading.Event()
        self.stopping = threading.Event()

        self.total_sent = 0
        self.total_send_failed = 0
        self.stats_lock = threading.Lock()

        self.publisher_thread = threading.Thread(
            target=self._publisher_loop,
            name="SQSBatchPublisher",
            daemon=True
        )
        self.publisher_thread.start()

        print("[SQS] Queue manager initialized with batch publishing.")

    def test_connection(self):
        try:
            response = self.sqs.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=["QueueArn"]
            )
            print("[SQS CONNECTION SUCCESSFUL]")
            print("Region:", self.region)
            print("Queue ARN:", response["Attributes"]["QueueArn"])
            return True

        except (ClientError, BotoCoreError) as error:
            print("[SQS CONNECTION FAILED]", error)
            raise

    def send_log(self, log):
        """Queue one log locally; publisher sends it in an SQS batch."""
        with self.pending_lock:
            self.pending_logs.append(log)
            should_flush = len(self.pending_logs) >= self.batch_size

        if should_flush:
            self.flush_event.set()

        return True

    def send_logs_batch(self, logs):
        """Send logs directly in SQS batches of at most 10."""
        sent = 0

        for start in range(0, len(logs), 10):
            group = logs[start:start + 10]

            entries = [
                {
                    "Id": str(index),
                    "MessageBody": json.dumps(log)
                }
                for index, log in enumerate(group)
            ]

            response = self.sqs.send_message_batch(
                QueueUrl=self.queue_url,
                Entries=entries
            )

            successful = response.get("Successful", [])
            failed = response.get("Failed", [])

            sent += len(successful)

            if failed:
                print("[SQS] Batch send failures:", failed)

            with self.stats_lock:
                self.total_sent += len(successful)
                self.total_send_failed += len(failed)

        return sent

    def _flush_pending(self):
        with self.pending_lock:
            if not self.pending_logs:
                return

            batch = self.pending_logs[:]
            self.pending_logs.clear()

        try:
            self.send_logs_batch(batch)

        except Exception as error:
            print("[SQS BATCH SEND ERROR]", error)

            # Put unsent logs back so they can be retried.
            with self.pending_lock:
                self.pending_logs = batch + self.pending_logs

            time.sleep(1)

    def _publisher_loop(self):
        while not self.stopping.is_set():
            self.flush_event.wait(self.flush_interval)
            self.flush_event.clear()
            self._flush_pending()

        self._flush_pending()

    def receive_messages(self, max_messages=10, wait_time_seconds=2):
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max(1, min(max_messages, 10)),
                WaitTimeSeconds=max(0, min(wait_time_seconds, 20)),
                AttributeNames=["All"]
            )

            return [
                {
                    "log": json.loads(message["Body"]),
                    "receipt_handle": message["ReceiptHandle"],
                    "message_id": message["MessageId"]
                }
                for message in response.get("Messages", [])
            ]

        except (ClientError, BotoCoreError, json.JSONDecodeError) as error:
            print("[SQS RECEIVE ERROR]", error)
            raise

    def delete_message(self, receipt_handle):
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            return True

        except (ClientError, BotoCoreError) as error:
            print("[SQS DELETE ERROR]", error)
            raise

    def get_queue_metrics(self):
        response = self.sqs.get_queue_attributes(
            QueueUrl=self.queue_url,
            AttributeNames=[
                "ApproximateNumberOfMessages",
                "ApproximateNumberOfMessagesNotVisible",
                "ApproximateNumberOfMessagesDelayed"
            ]
        )

        attributes = response["Attributes"]

        return {
            "messages_waiting": int(
                attributes.get("ApproximateNumberOfMessages", 0)
            ),
            "messages_processing": int(
                attributes.get("ApproximateNumberOfMessagesNotVisible", 0)
            ),
            "messages_delayed": int(
                attributes.get("ApproximateNumberOfMessagesDelayed", 0)
            )
        }

    def get_publisher_status(self):
        with self.pending_lock:
            pending = len(self.pending_logs)

        with self.stats_lock:
            sent = self.total_sent
            failed = self.total_send_failed

        return {
            "pending_local": pending,
            "total_sent": sent,
            "total_send_failed": failed
        }

    def stop(self):
        self.stopping.set()
        self.flush_event.set()

        if self.publisher_thread.is_alive():
            self.publisher_thread.join(timeout=10)