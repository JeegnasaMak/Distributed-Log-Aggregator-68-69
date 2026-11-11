# Distributed Log Aggregator & Indexer

## About the Project

The **Distributed Log Aggregator & Indexer** is a Python-based project that collects log messages from multiple servers and stores them in one place.

It generates logs from three simulated servers and processes them using a central queue and worker threads. The logs are stored in an SQLite database and can be searched and viewed through a web dashboard.

## Features

- Generates logs from three different servers.
- Supports INFO, WARNING and ERROR log levels.
- Uses a central queue to manage incoming logs.
- Processes logs using multiple worker threads.
- Stores logs in an SQLite database.
- Uses an inverted index for faster searching.
- Allows users to view and search stored logs.
- Displays log statistics and information through a web dashboard.

## Technologies Used

- **Python** – Main programming language.
- **Flask** – Connects the backend with the web dashboard.
- **SQLite** – Stores log records.
- **HTML** – Creates the dashboard structure.
- **CSS** – Designs the dashboard.
- **JavaScript** – Adds interactive features.
- **Multithreading** – Processes multiple logs using worker threads.

## Project Structure

```text
Distributed-Log-Aggregator/
│
├── src/
│   ├── app.py
│   ├── indexer.py
│   ├── log_generator.py
│   ├── main.py
│   ├── queue_manager.py
│   └── storage.py
│
├── static/
│   ├── script.js
│   └── style.css
│
├── templates/
│   └── index.html
│
├── requirements.txt
├── README.md
└── .gitignore
```

## How to Run the Project

1. Download or clone the repository.
2. Open the project folder in VS Code.
3. Create and activate a Python virtual environment.
4. Install the required packages:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Run the application:

   ```bash
   python src/app.py
   ```

6. Open the dashboard in your browser using the local URL displayed in the terminal.

## Expected Result

The application generates log messages from multiple servers, processes and stores them in a database, and displays them on a dashboard. Users can view log records, check statistics and search for specific logs.

## Conclusion

This project demonstrates how logs from multiple servers can be collected, processed, stored and searched using a single application. It helped us understand queues, multithreading, databases and log indexing.

---

**Project Name:** Distributed Log Aggregator & Indexer  
**Project Type:** Software System Design Micro Project
