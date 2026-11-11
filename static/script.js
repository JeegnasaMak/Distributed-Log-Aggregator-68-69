
let severityChart = null;
let serverChart = null;
let currentLogs = [];


// Safely display text
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}


// Load dashboard statistics
async function loadStats() {
    try {
        const response = await fetch("/api/stats");

        if (!response.ok) {
            throw new Error("Unable to load statistics");
        }

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
        console.error(error);
    }
}


// Create analytics charts
function updateCharts(data) {

    if (severityChart) severityChart.destroy();
    if (serverChart) serverChart.destroy();

    severityChart = new Chart(
        document.getElementById("severityChart"),
        {
            type: "doughnut",

            data: {
                labels: ["INFO", "WARNING", "ERROR"],

                datasets: [{
                    data: [
                        data.severity_counts.INFO,
                        data.severity_counts.WARNING,
                        data.severity_counts.ERROR
                    ],

                    backgroundColor: [
                        "#3B82F6",
                        "#F59E0B",
                        "#EF4444"
                    ],

                    borderWidth: 3,
                    borderColor: "#FFFFFF"
                }]
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom"
                    }
                }
            }
        }
    );


    serverChart = new Chart(
        document.getElementById("serverChart"),
        {
            type: "bar",

            data: {
                labels: [
                    "SERVER-1",
                    "SERVER-2",
                    "SERVER-3"
                ],

                datasets: [{
                    label: "Number of Logs",

                    data: [
                        data.server_counts["SERVER-1"],
                        data.server_counts["SERVER-2"],
                        data.server_counts["SERVER-3"]
                    ],

                    backgroundColor: [
                        "#2563EB",
                        "#60A5FA",
                        "#93C5FD"
                    ],

                    borderRadius: 7
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


// Load logs using search and filters
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

        if (!response.ok) {
            throw new Error("Unable to load logs");
        }

        const data = await response.json();

        currentLogs = data.logs;

        const table = document.getElementById("logsTable");

        document.getElementById("logCountLabel").textContent =
            data.count + " records";

        if (data.logs.length === 0) {

            table.innerHTML = `
                <tr>
                    <td colspan="6">No matching logs found.</td>
                </tr>
            `;

            return;
        }

        table.innerHTML = data.logs.map(log => `
            <tr>
                <td>${log.id}</td>

                <td>${escapeHTML(log.timestamp)}</td>

                <td>${escapeHTML(log.server)}</td>

                <td>
                    <span class="severity ${escapeHTML(log.level)}">
                        ${escapeHTML(log.level)}
                    </span>
                </td>

                <td>${escapeHTML(log.message)}</td>

                <td>
                    <button class="view-btn"
                        onclick="showLogDetails(${log.id})">
                        View
                    </button>
                </td>
            </tr>
        `).join("");

    } catch (error) {
        console.error(error);
    }
}


// FUNCTIONALITY 1: Export filtered logs to CSV
function exportLogs() {

    if (currentLogs.length === 0) {
        alert("No logs available to export!");
        return;
    }

    const headers = [
        "ID",
        "Timestamp",
        "Server",
        "Severity",
        "Message"
    ];

    const rows = currentLogs.map(log => [
        log.id,
        log.timestamp,
        log.server,
        log.level,
        log.message
    ]);

    const csvContent = [headers, ...rows]
        .map(row => row.map(value =>
            `"${String(value ?? "").replace(/"/g, '""')}"`
        ).join(","))
        .join("\r\n");

    const blob = new Blob(
        ["\uFEFF" + csvContent],
        { type: "text/csv;charset=utf-8;" }
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "LogPulse_Logs.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}


// FUNCTIONALITY 2: Clear all stored logs
async function clearAllLogs() {

    const confirmed = confirm(
        "Are you sure you want to delete ALL stored logs? This cannot be undone."
    );

    if (!confirmed) return;

    try {

        const response = await fetch("/api/clear", {
            method: "POST"
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to clear logs");
        }

        alert(data.message);

        clearFilters();
        await refreshDashboard();

    } catch (error) {
        alert(error.message);
    }
}


// FUNCTIONALITY 3: Show error alerts
async function loadErrorAlerts() {

    try {

        const response = await fetch("/api/logs?level=ERROR");

        if (!response.ok) {
            throw new Error("Unable to load error alerts");
        }

        const data = await response.json();

        const errors = data.logs.slice(0, 5);

        document.getElementById("alertCount").textContent =
            data.count + " Errors";

        const errorList = document.getElementById("errorList");

        if (errors.length === 0) {

            errorList.innerHTML = `
                <p class="no-errors">
                    ✓ No errors detected. System looks good!
                </p>
            `;

            return;
        }

        errorList.innerHTML = errors.map(log => `
            <div class="error-item">

                <div class="error-top">
                    <strong>🔴 ${escapeHTML(log.server)}</strong>
                    <span>${escapeHTML(log.timestamp)}</span>
                </div>

                <p>${escapeHTML(log.message)}</p>

                <small>Log ID: ${log.id}</small>

            </div>
        `).join("");

    } catch (error) {
        console.error(error);
    }
}


// FUNCTIONALITY 4: View complete log details
function showLogDetails(id) {

    const log = currentLogs.find(item => item.id === id);

    if (!log) {
        alert("Log details not found.");
        return;
    }

    document.getElementById("logDetails").innerHTML = `

        <div class="detail-item">
            <label>Log ID</label>
            <strong>${log.id}</strong>
        </div>

        <div class="detail-item">
            <label>Timestamp</label>
            <strong>${escapeHTML(log.timestamp)}</strong>
        </div>

        <div class="detail-item">
            <label>Server</label>
            <strong>${escapeHTML(log.server)}</strong>
        </div>

        <div class="detail-item">
            <label>Severity Level</label>
            <strong>
                <span class="severity ${escapeHTML(log.level)}">
                    ${escapeHTML(log.level)}
                </span>
            </strong>
        </div>

        <div class="detail-item">
            <label>Log Message</label>
            <strong>${escapeHTML(log.message)}</strong>
        </div>
    `;

    document.getElementById("logModal").style.display = "flex";
}


// Close log details popup
function closeLogDetails() {
    document.getElementById("logModal").style.display = "none";
}


// Close popup when clicking outside
function closeModalOutside(event) {

    if (event.target.id === "logModal") {
        closeLogDetails();
    }
}


// Generate new logs
async function generateLogs() {

    const count = Number(
        document.getElementById("logCount").value
    );

    const message =
        document.getElementById("generateMessage");

    const button =
        document.querySelector(".generate-controls button");

    if (!Number.isInteger(count) || count < 1 || count > 1000) {

        message.textContent =
            "Enter a number between 1 and 1000.";

        message.style.color = "#DC2626";
        return;
    }

    button.disabled = true;
    button.textContent = "Generating...";

    message.textContent =
        "Processing logs through worker threads...";

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
            throw new Error(data.error || "Generation failed");
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


// Clear search filters
function clearFilters() {

    document.getElementById("keyword").value = "";
    document.getElementById("levelFilter").value = "";
    document.getElementById("serverFilter").value = "";

    loadLogs();
}


// Refresh complete dashboard
async function refreshDashboard() {

    await loadStats();
    await loadLogs();
    await loadErrorAlerts();
}


// Dashboard startup
document.addEventListener("DOMContentLoaded", () => {

    refreshDashboard();

    // Automatic refresh every 10 seconds
    setInterval(refreshDashboard, 10000);

});