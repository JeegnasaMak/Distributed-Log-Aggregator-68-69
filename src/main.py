
from log_generator import generate_multiple_logs
from storage import (
    initialize_database,
    get_all_logs,
    get_logs_by_ids,
    get_logs_by_filter
)
from queue_manager import process_logs
from indexer import build_index, search_keyword


def display_logs(logs):
    """Display log records in a readable format."""

    if not logs:
        print("\nNo matching logs found.")
        return

    for log in logs:
        print("\nLog ID:", log[0])
        print("Timestamp:", log[1])
        print("Server:", log[2])
        print("Level:", log[3])
        print("Message:", log[4])


def main():
    print("===================================")
    print("      DISTRIBUTED LOG AGGREGATOR")
    print("===================================")

    # Initialize database
    initialize_database()
    print("\nDatabase initialized successfully!")

    # Generate logs
    try:
        count = int(input("\nHow many logs should be generated? "))

        if count <= 0:
            print("Enter a number greater than zero.")
            return

    except ValueError:
        print("Invalid input! Enter a whole number.")
        return

    print(f"\nGenerating {count} logs...")
    generated_logs = generate_multiple_logs(count)

    print(f"{len(generated_logs)} new logs generated successfully!")

    # Process logs using multiple workers
    process_logs(generated_logs, worker_count=3)

    # Build inverted index
    build_index()

    # Display database summary
    all_logs = get_all_logs()

    print("\n===================================")
    print(f"Logs generated in this run: {len(generated_logs)}")
    print(f"Total logs stored: {len(all_logs)}")
    print("===================================")

    # Log search and filtering menu
    while True:
        print("\n========== LOG SEARCH ==========")
        print("1. Search logs by keyword")
        print("2. Filter logs by severity")
        print("3. Filter logs by server")
        print("4. Display all stored logs")
        print("5. Exit")

        choice = input("\nEnter your choice: ").strip()

        # Keyword search using inverted index
        if choice == "1":
            keyword = input("Enter keyword: ").strip()

            matching_ids = search_keyword(keyword)
            matching_logs = get_logs_by_ids(matching_ids)

            print(f"\nFound {len(matching_logs)} matching logs:")
            display_logs(matching_logs)

        # Filter by severity
        elif choice == "2":
            level = input(
                "Enter severity (INFO/WARNING/ERROR): "
            ).strip().upper()

            if level not in ["INFO", "WARNING", "ERROR"]:
                print("Invalid severity level!")
                continue

            matching_logs = get_logs_by_filter(level=level)

            print(f"\nFound {len(matching_logs)} matching logs:")
            display_logs(matching_logs)

        # Filter by server
        elif choice == "3":
            server = input(
                "Enter server (SERVER-1/SERVER-2/SERVER-3): "
            ).strip().upper()

            if server not in ["SERVER-1", "SERVER-2", "SERVER-3"]:
                print("Invalid server!")
                continue

            matching_logs = get_logs_by_filter(server=server)

            print(f"\nFound {len(matching_logs)} matching logs:")
            display_logs(matching_logs)

        # Display all logs
        elif choice == "4":
            all_logs = get_all_logs()
            print(f"\nTotal stored logs: {len(all_logs)}")
            display_logs(all_logs)

        # Exit
        elif choice == "5":
            print("\nExiting Log Aggregator. Thank you!")
            break

        else:
            print("\nInvalid choice! Please select 1-5.")


if __name__ == "__main__":
    main()