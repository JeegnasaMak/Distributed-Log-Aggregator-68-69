
let severityChart = null;
let serverChart = null;
let currentLogs = [];


// --------------------------------------------------
// SAFE HTML DISPLAY
// --------------------------------------------------

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}


// --------------------------------------------------
// LOAD STATISTICS
// --------------------------------------------------

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
        console.error("Statistics error:", error);
    }
}


// --------------------------------------------------
// CHARTS
// --------------------------------------------------

function updateCharts(data) {

    const severityData = [
        data.severity_counts.INFO,
        data.severity_counts.WARNING,
        data.severity_counts.ERROR
    ];

    const serverData = [
        data.server_counts["SERVER-1"],
        data.server_counts["SERVER-2"],
        data.server_counts["SERVER-3"]
    ];

    if (!severityChart) {

        severityChart = new Chart(
            document.getElementById("severityChart"),
            {
                type: "doughnut",
                data: {
                    labels: ["INFO", "WARNING", "ERROR"],
                    datasets: [{
                        data: severityData,
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

    } else {

        severityChart.data.datasets[0].data = severityData;
        severityChart.update();
    }

    if (!serverChart) {

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
                        data: serverData,
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

    } else {

        serverChart.data.datasets[0].data = serverData;
        serverChart.update();
    }
}


// --------------------------------------------------
// LIVE SYSTEM MONITOR
// --------------------------------------------------

async function loadSystemStatus() {

    try {

        const response = await fetch("/api/system");

        if (!response.ok) {
            throw new Error("Unable to load system status");
        }

        const data = await response.json();

        const workers = data.workers;
        const queue = data.queue;
        const workload = data.workload;

        document.getElementById("activeWorkers").textContent =
            workers.active_workers ?? 0;

        document.getElementById("workerCountLabel").textContent =
            workers.active_workers ?? 0;

        document.getElementById("processedLogs").textContent =
            workers.total_processed ?? 0;

        document.getElementById("failedLogs").textContent =
            workers.total_failed ?? 0;

        document.getElementById("waitingMessages").textContent =
            queue.messages_waiting ?? 0;

        document.getElementById("processingMessages").textContent =
            queue.messages_processing ?? 0;

        document.getElementById("generatedLogs").textContent =
            workload.total_generated ?? 0;

        document.getElementById("workloadRate").textContent =
            workload.current_rate ?? 0;

        const phase = String(
            workload.current_phase || "NORMAL"
        ).toUpperCase();

        document.getElementById("workloadPhase").textContent =
            phase;

        document.getElementById("workloadDescription").textContent =
            getPhaseDescription(phase);

        updatePhaseTrack(phase);
        updateWorkerCards(workers.active_workers ?? 0);

        const systemStatus = document.getElementById("systemStatus");
        const sidebarText = document.getElementById("sidebarStatusText");
        const sidebarDot = document.getElementById("sidebarStatusDot");

        if (data.system_running && workers.running) {

            systemStatus.textContent = "SYSTEM RUNNING";
            systemStatus.className = "system-pill online";

            sidebarText.textContent = "System Active";
            sidebarDot.classList.add("online");

        } else {

            systemStatus.textContent = "SYSTEM STOPPED";
            systemStatus.className = "system-pill offline";

            sidebarText.textContent = "System Offline";
            sidebarDot.classList.remove("online");
        }

    } catch (error) {
        console.error("System monitor error:", error);

        document.getElementById("systemStatus").textContent =
            "CONNECTION ERROR";
    }
}


// --------------------------------------------------
// WORKLOAD PHASE DESCRIPTION
// --------------------------------------------------

function getPhaseDescription(phase) {

    const descriptions = {
        NORMAL: "Normal log generation. Minimum workers handle the workload.",
        INCREASING: "Incoming log volume is increasing. Workers monitor the backlog.",
        SPIKE: "A sudden increase in log generation is being simulated.",
        HEAVY: "Heavy workload. Additional workers can be created automatically.",
        DECREASING: "Workload is decreasing. Extra workers can be stopped."
    };

    return descriptions[phase] || "Monitoring automatic workload.";
}


// --------------------------------------------------
// WORKLOAD PHASE TRACK
// --------------------------------------------------

function updatePhaseTrack(phase) {

    document.querySelectorAll(".phase-step").forEach(step => {

        step.classList.remove("phase-active");

        if (step.dataset.phase === phase) {
            step.classList.add("phase-active");
        }
    });
}


// --------------------------------------------------
// WORKER SIMULATION CARDS
// --------------------------------------------------

function updateWorkerCards(workerCount) {

    const grid = document.getElementById("workerGrid");

    if (!grid) return;

    if (workerCount <= 0) {

        grid.innerHTML = `
            <div class="empty-worker">
                No active workers at the moment.
            </div>
        `;

        return;
    }

    const cards = [];

    for (let i = 1; i <= workerCount; i++) {

        cards.push(`
            <div class="worker-card">
                <div class="worker-card-top">
                    <div class="worker-icon">⚙</div>
                    <span class="worker-live">
                        <span class="worker-dot"></span>
                        ACTIVE
                    </span>
                </div>

                <h3>Worker ${i}</h3>

                <p>Python processing thread</p>

                <div class="worker-card-bottom">
                    <span>Amazon SQS</span>
                    <strong>Running</strong>
                </div>
            </div>
        `);
    }

    grid.innerHTML = cards.join("");
}


// --------------------------------------------------
// READ FILTER VALUES
// --------------------------------------------------

function getLogFilters() {

    const keywordElement = document.getElementById("keyword");
    const levelElement = document.getElementById("levelFilter");
    const serverElement = document.getElementById("serverFilter");

    const keyword = keywordElement
        ? keywordElement.value.trim()
        : "";

    let level = levelElement
        ? levelElement.value.trim().toUpperCase()
        : "";

    let server = serverElement
        ? serverElement.value.trim().toUpperCase()
        : "";

    if (["ALL", "ALL LEVELS", "NONE"].includes(level)) {
        level = "";
    }

    if (["ALL", "ALL SERVERS", "NONE"].includes(server)) {
        server = "";
    }

    return { keyword, level, server };
}


// --------------------------------------------------
// LOAD LOGS WITH FILTERS
// --------------------------------------------------

async function loadLogs() {

    try {

        const filters = getLogFilters();

        const params = new URLSearchParams();

        if (filters.keyword) {
            params.set("keyword", filters.keyword);
        }

        if (filters.level) {
            params.set("level", filters.level);
        }

        if (filters.server) {
            params.set("server", filters.server);
        }

        const query = params.toString();

        const response = await fetch(
            "/api/logs" + (query ? "?" + query : ""),
            { cache: "no-store" }
        );

        if (!response.ok) {
            throw new Error("Unable to load logs");
        }

        const data = await response.json();

        currentLogs = data.logs || [];

        const table = document.getElementById("logsTable");
        const countLabel = document.getElementById("logCountLabel");

        countLabel.textContent = data.count + " records";

        if (currentLogs.length === 0) {

            table.innerHTML = `
                <tr>
                    <td colspan="6">No matching logs found.</td>
                </tr>
            `;

            return;
        }

        table.innerHTML = currentLogs.map(log => `

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
        console.error("Log loading error:", error);
    }
}


// --------------------------------------------------
// SEARCH BUTTON
// --------------------------------------------------

function searchLogs() {
    loadLogs();
}


// --------------------------------------------------
// ERROR ALERTS
// --------------------------------------------------

async function loadErrorAlerts() {

    try {

        const response = await fetch(
            "/api/logs?level=ERROR",
            { cache: "no-store" }
        );

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
        console.error("Error alert loading error:", error);
    }
}


// --------------------------------------------------
// VIEW LOG DETAILS
// --------------------------------------------------

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


function closeLogDetails() {
    document.getElementById("logModal").style.display = "none";
}


function closeModalOutside(event) {

    if (event.target.id === "logModal") {
        closeLogDetails();
    }
}


// --------------------------------------------------
// EXPORT CSV
// --------------------------------------------------

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
    link.download = "Distributed_Logs.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
}


// --------------------------------------------------
// CLEAR FILTERS
// --------------------------------------------------

function clearFilters() {

    document.getElementById("keyword").value = "";
    document.getElementById("levelFilter").value = "";
    document.getElementById("serverFilter").value = "";

    loadLogs();
}


// --------------------------------------------------
// CLEAR DATABASE LOGS
// --------------------------------------------------

async function clearAllLogs() {

    const confirmed = confirm(
        "Clear all currently stored database logs? New incoming logs will continue."
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


// --------------------------------------------------
// REFRESH DASHBOARD
// --------------------------------------------------

async function refreshDashboard() {

    await Promise.all([
        loadStats(),
        loadSystemStatus(),
        loadLogs(),
        loadErrorAlerts()
    ]);
}


// --------------------------------------------------
// DASHBOARD STARTUP
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {

    // Search button can call searchLogs() directly.
    const searchButton = document.querySelector(
        'button[onclick="loadLogs()"], button[onclick="searchLogs()"]'
    );

    if (searchButton) {
        searchButton.onclick = searchLogs;
    }

    // Press Enter in keyword box to search.
    const keywordInput = document.getElementById("keyword");

    if (keywordInput) {
        keywordInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                searchLogs();
            }
        });
    }

    refreshDashboard();

    setInterval(loadSystemStatus, 3000);
    setInterval(refreshDashboard, 5000);

});