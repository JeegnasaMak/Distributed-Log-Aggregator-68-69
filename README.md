# Distributed Log Aggregator & Indexer

## About the Project

The **Distributed Log Aggregator & Indexer** is a system that collects, stores, and manages log messages from multiple servers in one place.

In this project, logs are generated from three different servers. Each log contains a timestamp, server name, log level, and message.

The system stores these logs and helps users view and search them easily through a simple web dashboard.

## Features

- Generates logs from multiple servers.
- Supports three log levels: INFO, WARNING, and ERROR.
- Stores log messages in a database.
- Helps search and manage stored logs.
- Displays log information on a simple dashboard.
- Shows useful log details in one place.

## Technologies Used

- **Python** – Main programming language.
- **HTML** – Creates the dashboard structure.
- **CSS** – Designs the dashboard.
- **JavaScript** – Adds actions to the dashboard.
- **SQLite** – Stores log data.

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
└── README.md
```

## How to Run the Project

1. Download or clone this repository.
2. Open the project folder in VS Code.
3. Install the required Python packages.
4. Run the application using the main Python file.
5. Open the dashboard in your browser.

## Expected Result

The system generates log messages from multiple servers, stores them, and displays the information on a web dashboard. Users can view and search the logs from one place.

## Conclusion

This project helps us understand how logs from different servers can be collected and managed using a single system. It also shows how Python, databases, and web technologies can work together.

---

**Project Name:** Distributed Log Aggregator & Indexer  
**Project Type:** Software System Design Micro Project
