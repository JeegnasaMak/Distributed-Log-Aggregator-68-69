
let severityChart = null;
let serverChart = null;


// Load dashboard statistics
async function loadStats() {
    try {
        const response = await fetch("/api/stats");
        const data = await response.json();

        document.getElementById("totalLogs").textContent =
            data.total_logs;

        document.getElementById("infoLogs").textContent =
            data.severity_counts.INFO;

        document.getElementById("warningLogs").textContent =
            data.severity_counts.WARNING;

        document.getElementById("errorLogs").textContent =
            data.severity_counts.ERROR;

        updateCharts(data);

    } catch (error) {
        console.error("Error loading statistics:", error);
    }
}


// Create or update analytics charts
function updateCharts(data) {

    const severityData = data.severity_counts;
    const serverData = data.server_counts;

    if (severityChart) {
        severityChart.destroy();
    }

    if (serverChart) {
        serverChart.destroy();
    }

    severityChart = new Chart(
        document.getElementById("severityChart"),
        {
            type: "doughnut",
            data: {
                labels: ["INFO", "WARNING", "ERROR"],
                datasets: [{
                    data: [
                        severityData.INFO,
                        severityData.WARNING,
                        severityData.ERROR
                    ],
                    backgroundColor: [
                        "#3B82F6",
                        "#F59E0B",
                        "#EF4444"
                    ],
                    borderWidth: 2,
                    borderColor: "#FFFFFF"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        }
    );

    serverChart = new Chart(
        document.getElementById("serverChart"),
        {
            type: "bar",
            data: {
                labels: ["SERVER-1", "SERVER-2", "SERVER-3"],
                datasets: [{
                    label: "Number of Logs",
                    data: [
                        serverData["SERVER-1"],
                        serverData["SERVER-2"],
                        serverData["SERVER-3"]
                    ],
                    backgroundColor: [
                        "#2563EB",
                        "#60A5FA",
                        "#93C5FD"
                    ],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        }
    );
}


// Load and display logs
async function loadLogs() {
    try {
        const keyword =
            document.getElementById("keyword").value.trim();

        const level =
            document.getElementById("levelFilter").value;

        const server =
            document.getElementById("serverFilter").value;

        const params = new URLSearchParams();

        if (keyword) params.append("keyword", keyword);
        if (level) params.append("level", level);
        if (server) params.append("server", server);

        const response = await fetch("/api/logs?" + params);
        const data = await response.json();

        const table = document.getElementById("logsTable");

        document.getElementById("logCountLabel").textContent =
            data.count + " records";

        if (data.logs.length === 0) {
            table.innerHTML = `
                <tr>
                    <td colspan="5">No matching logs found.</td>
                </tr>
            `;
            return;
        }

        table.innerHTML = data.logs.map(log => `
            <tr>
                <td>${log.id}</td>
                <td>${log.timestamp}</td>
                <td>${log.server}</td>
                <td>
                    <span class="severity ${log.level}">
                        ${log.level}
                    </span>
                </td>
                <td>${log.message}</td>
            </tr>
        `).join("");

    } catch (error) {
        console.error("Error loading logs:", error);
    }
}


// Generate logs from dashboard
async function generateLogs() {
    const count = Number(
        document.getElementById("logCount").value
    );

    const message = document.getElementById("generateMessage");
    const button = document.querySelector(".generate-controls button");

    if (!Number.isInteger(count) || count < 1 || count > 1000) {
        message.textContent = "Enter a number between 1 and 1000.";
        message.style.color = "#DC2626";
        return;
    }

    button.disabled = true;
    button.textContent = "Generating...";

    message.textContent = "Processing logs through workers...";
    message.style.color = "#2563EB";

    try {
        const response = await fetch("/api/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ count: count })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Generation failed.");
        }

        message.textContent =
            `${data.generated} logs generated successfully! Total stored: ${data.total_logs}`;

        message.style.color = "#15803D";

        await refreshDashboard();

    } catch (error) {
        message.textContent = error.message;
        message.style.color = "#DC2626";

    } finally {
        button.disabled = false;
        button.textContent = "+ Generate Logs";
    }
}


// Clear all search filters
function clearFilters() {
    document.getElementById("keyword").value = "";
    document.getElementById("levelFilter").value = "";
    document.getElementById("serverFilter").value = "";

    loadLogs();
}


// Refresh dashboard
async function refreshDashboard() {
    await loadStats();
    await loadLogs();
}


// Initial dashboard loading
document.addEventListener("DOMContentLoaded", () => {
    refreshDashboard();

    // Refresh statistics and logs every 10 seconds
    setInterval(refreshDashboard, 10000);
});