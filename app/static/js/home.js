// Deal with datetime defaults for task forms.
function addZero(num) {
    return num < 10 ? "0" + num : String(num);
}

function setNowForTaskInputs() {
    var now = new Date();
    var datetimeValue =
        now.getFullYear() +
        "-" +
        addZero(now.getMonth() + 1) +
        "-" +
        addZero(now.getDate()) +
        "T" +
        addZero(now.getHours()) +
        ":" +
        addZero(now.getMinutes());

    var deadlineInput = document.getElementById("setdead");
    var remindInput = document.getElementById("setremind");

    if (deadlineInput) {
        deadlineInput.setAttribute("value", datetimeValue);
    }
    if (remindInput) {
        remindInput.setAttribute("value", datetimeValue);
    }
}

function setError(element, message) {
    var inputControl = element.parentElement;
    var errorDisplay = inputControl.querySelector(".error-message");
    if (!errorDisplay) {
        return;
    }
    errorDisplay.innerText = message;
    inputControl.classList.add("error-message");
}

function clearError(element) {
    var inputControl = element.parentElement;
    var errorDisplay = inputControl.querySelector(".error-message");
    if (!errorDisplay) {
        return;
    }
    errorDisplay.innerText = "";
    inputControl.classList.remove("error-message");
}

function bindCreateTaskValidation() {
    var form = document.getElementById("form");
    var moduleInput = document.getElementById("create-list-input");
    var assessmentInput = document.getElementById("create-task-input");

    if (!form || !moduleInput || !assessmentInput) {
        return;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        clearError(moduleInput);
        clearError(assessmentInput);

        var moduleValue = moduleInput.value.trim();
        var assessmentValue = assessmentInput.value.trim();

        if (!moduleValue) {
            setError(moduleInput, "Module must be entered!");
            return;
        }

        if (!assessmentValue) {
            setError(assessmentInput, "Assessment must be entered!");
            return;
        }

        form.submit();
    });
}

function logout() {
    window.location.href = window.location.origin + "/newlogin";
}

function showToastIfPresent() {
    var toastEl = document.querySelector(".toast");
    if (!toastEl || !window.bootstrap || !window.bootstrap.Toast) {
        return;
    }

    new bootstrap.Toast(toastEl).show();
    window.setTimeout(function () {
        toastEl.classList.remove("show");
    }, 5000);
}

function bindToastActions() {
    var createBtn = document.querySelector("#liveToastBtn");
    if (createBtn) {
        createBtn.addEventListener("click", showToastIfPresent);
    }

    var inTaskButtons = document.querySelectorAll(".in-task-link");
    inTaskButtons.forEach(function (btn) {
        btn.addEventListener("click", showToastIfPresent);
    });
}

function bindPopovers() {
    if (!window.bootstrap || !window.bootstrap.Popover) {
        return;
    }

    var popoverTriggerList = Array.prototype.slice.call(
        document.querySelectorAll('[data-bs-toggle="popover"]')
    );
    popoverTriggerList.forEach(function (popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl);
    });
}

function setMetricValue(elementId, value, suffix) {
    var target = document.getElementById(elementId);
    if (!target) {
        return;
    }

    var finalSuffix = suffix || "";
    target.textContent = String(value) + finalSuffix;
}

function setInsightSummary(kpis) {
    var summary = document.getElementById("insight-summary");
    if (!summary) {
        return;
    }

    var completionRate = Number(kpis.completion_rate || 0);
    var urgentOpen = Number(kpis.urgent_open || 0);
    var overdueRate = Number(kpis.overdue_rate || 0);
    var tone = "Execution is balanced";

    if (urgentOpen >= 2 || overdueRate > 20) {
        tone = "Risk pressure is elevated";
    } else if (completionRate >= 65 && overdueRate <= 10) {
        tone = "Delivery momentum is strong";
    }

    summary.textContent =
        tone +
        " - completion " + completionRate.toFixed(1) +
        "%, urgent " + urgentOpen +
        ", overdue " + overdueRate.toFixed(1) +
        "%.";
}

function setInsightSyncStamp(isSuccess) {
    var syncLine = document.getElementById("insight-last-sync");
    if (!syncLine) {
        return;
    }

    var now = new Date();
    var stamp =
        addZero(now.getHours()) +
        ":" +
        addZero(now.getMinutes()) +
        ":" +
        addZero(now.getSeconds());

    syncLine.textContent = "Last synced: " + stamp + (isSuccess ? "" : " (degraded)");
    syncLine.classList.toggle("is-degraded", !isSuccess);
}

function parseIsoLikeTimestamp(raw) {
    if (!raw || typeof raw !== "string") {
        return null;
    }

    var normalized = raw.endsWith("Z") ? raw : raw + "Z";
    var parsed = new Date(normalized);
    if (Number.isNaN(parsed.getTime())) {
        return null;
    }
    return parsed;
}

function formatSyncTimeForDisplay(raw) {
    var parsed = parseIsoLikeTimestamp(raw);
    if (!parsed) {
        return null;
    }

    return (
        addZero(parsed.getHours()) +
        ":" +
        addZero(parsed.getMinutes()) +
        ":" +
        addZero(parsed.getSeconds())
    );
}

function setInsightSyncStampFromPayload(primaryTimestamp, fallbackTimestamp) {
    var syncLine = document.getElementById("insight-last-sync");
    if (!syncLine) {
        return;
    }

    var display = formatSyncTimeForDisplay(primaryTimestamp) || formatSyncTimeForDisplay(fallbackTimestamp);
    if (!display) {
        setInsightSyncStamp(true);
        return;
    }

    syncLine.textContent = "Last synced: " + display;
    syncLine.classList.remove("is-degraded");
}

function resolveApiErrorMessage(response, payload) {
    if (payload && payload.error_detail && payload.error_detail.message) {
        return String(payload.error_detail.message);
    }
    if (payload && payload.error) {
        return String(payload.error);
    }
    if (response && response.status) {
        return "Request failed with status " + response.status + ".";
    }
    return "Failed to load dashboard insights.";
}

var priorityChartInstance = null;
var timelineChartInstance = null;
var chartResizeBound = false;
var isInsightsLoading = false;

function bindChartResize() {
    if (chartResizeBound || !window.echarts) {
        return;
    }

    window.addEventListener("resize", function () {
        if (priorityChartInstance) {
            priorityChartInstance.resize();
        }
        if (timelineChartInstance) {
            timelineChartInstance.resize();
        }
    });
    chartResizeBound = true;
}

function getChartInstance(chartEl, previousInstance) {
    if (!chartEl || !window.echarts) {
        return null;
    }

    if (previousInstance) {
        previousInstance.dispose();
    }
    return echarts.init(chartEl);
}

function setHealthBadge(kpis) {
    var badge = document.getElementById("insight-health");
    if (!badge) {
        return;
    }

    var completionRate = Number(kpis.completion_rate || 0);
    var overdueRate = Number(kpis.overdue_rate || 0);
    var statusText = "Healthy";
    var statusClass = "is-good";

    if (overdueRate > 25 || completionRate < 35) {
        statusText = "Needs Attention";
        statusClass = "is-risk";
    } else if (overdueRate > 10 || completionRate < 55) {
        statusText = "Watchlist";
        statusClass = "is-warn";
    }

    badge.textContent = statusText;
    badge.classList.remove("is-good", "is-warn", "is-risk");
    badge.classList.add(statusClass);
}

function renderModuleSpotlight(moduleDistribution, moduleHotspots) {
    var list = document.getElementById("insight-module-list");
    if (!list) {
        return;
    }

    var hotspots = (moduleHotspots || []).map(function (item) {
        return {
            name: item && item.name ? String(item.name) : "",
            count: Number(item && item.count ? item.count : 0),
        };
    }).filter(function (item) {
        return item.name;
    });

    var rows = hotspots;
    if (!rows.length) {
        rows = Object.keys(moduleDistribution || {}).map(function (name) {
            return { name: name, count: Number(moduleDistribution[name] || 0) };
        });
        rows.sort(function (a, b) {
            if (b.count !== a.count) {
                return b.count - a.count;
            }
            return a.name.localeCompare(b.name);
        });
    }

    list.innerHTML = "";
    if (!rows.length) {
        var empty = document.createElement("li");
        empty.textContent = "No module activity yet.";
        list.appendChild(empty);
        return;
    }

    rows.slice(0, 3).forEach(function (row) {
        var li = document.createElement("li");
        li.textContent = row.name + " : " + row.count + " task(s)";
        list.appendChild(li);
    });
}

function renderTrendStrip(timelineItems) {
    var strip = document.getElementById("insight-trend-strip");
    if (!strip) {
        return;
    }

    strip.innerHTML = "";

    var items = timelineItems || [];
    if (!items.length) {
        var emptyHint = document.createElement("p");
        emptyHint.className = "insight-trend-empty";
        emptyHint.textContent = "No recent deadline activity.";
        strip.appendChild(emptyHint);
        return;
    }

    var maxCount = 0;
    items.forEach(function (item) {
        if (item.count > maxCount) {
            maxCount = item.count;
        }
    });
    if (!maxCount) {
        maxCount = 1;
    }

    items.forEach(function (item) {
        var point = document.createElement("span");
        point.className = "trend-point";
        point.style.setProperty("--bar-height", Math.max(9, Math.round((item.count / maxCount) * 100)) + "%");
        point.setAttribute("title", item.date + ": " + item.count + " task(s)");
        point.setAttribute("aria-label", item.date + " has " + item.count + " task(s)");
        strip.appendChild(point);
    });
}

function renderHeatmap(timelineItems) {
    var heatmap = document.getElementById("insight-heatmap");
    if (!heatmap) {
        return;
    }

    heatmap.innerHTML = "";
    var items = timelineItems || [];
    if (!items.length) {
        var empty = document.createElement("p");
        empty.className = "insight-trend-empty";
        empty.textContent = "No heatmap data yet.";
        heatmap.appendChild(empty);
        return;
    }

    var max = 0;
    items.forEach(function (item) {
        if (item.count > max) {
            max = item.count;
        }
    });
    if (!max) {
        max = 1;
    }

    items.forEach(function (item) {
        var cell = document.createElement("span");
        var ratio = item.count / max;
        var level = 0;
        if (ratio > 0.75) {
            level = 4;
        } else if (ratio > 0.5) {
            level = 3;
        } else if (ratio > 0.25) {
            level = 2;
        } else if (ratio > 0) {
            level = 1;
        }
        cell.className = "heat-cell lvl-" + level;
        cell.setAttribute("title", item.date + " : " + item.count + " task(s)");
        cell.setAttribute("aria-label", item.date + " workload level " + level);
        heatmap.appendChild(cell);
    });
}

function setFocusRecommendations(kpis) {
    var list = document.getElementById("insight-focus-list");
    if (!list) {
        return;
    }

    var recommendations = [];
    var urgentOpen = Number(kpis.urgent_open || 0);
    var upcoming = Number(kpis.upcoming_7_days || 0);
    var completionRate = Number(kpis.completion_rate || 0);
    var overdueRate = Number(kpis.overdue_rate || 0);

    if (urgentOpen > 0) {
        recommendations.push("Prioritize " + urgentOpen + " urgent open task(s) before adding new items.");
    }
    if (upcoming >= 3) {
        recommendations.push("Review upcoming deadlines and pre-split complex tasks into smaller chunks.");
    }
    if (completionRate < 45) {
        recommendations.push("Completion rate is low. Reserve one uninterrupted focus block today.");
    }
    if (overdueRate > 20) {
        recommendations.push("Overdue rate is elevated. Clear oldest overdue item first to recover momentum.");
    }
    if (!recommendations.length) {
        recommendations.push("Execution looks healthy. Keep a steady cadence and protect deep-work windows.");
        recommendations.push("Use the visualization tools to spot the next bottleneck early.");
    }

    list.innerHTML = "";
    recommendations.slice(0, 3).forEach(function (text) {
        var li = document.createElement("li");
        li.textContent = text;
        list.appendChild(li);
    });
}

function setRiskAlerts(kpis) {
    var list = document.getElementById("insight-alert-list");
    if (!list) {
        return;
    }

    var alerts = [];
    var urgentOpen = Number(kpis.urgent_open || 0);
    var overdueRate = Number(kpis.overdue_rate || 0);
    var completionRate = Number(kpis.completion_rate || 0);
    var upcoming = Number(kpis.upcoming_7_days || 0);

    if (urgentOpen >= 2) {
        alerts.push("High urgency load detected: " + urgentOpen + " urgent task(s) open.");
    }
    if (overdueRate >= 20) {
        alerts.push("Overdue risk elevated: " + overdueRate.toFixed(1) + "% overdue rate.");
    }
    if (completionRate <= 40) {
        alerts.push("Execution throughput low: completion rate at " + completionRate.toFixed(1) + "%.");
    }
    if (upcoming >= 5) {
        alerts.push("Deadline congestion ahead: " + upcoming + " items due in 7 days.");
    }

    if (!alerts.length) {
        alerts.push("No critical risk detected. Current delivery rhythm is stable.");
    }

    list.innerHTML = "";
    alerts.slice(0, 3).forEach(function (text) {
        var li = document.createElement("li");
        li.textContent = text;
        list.appendChild(li);
    });
}

function renderPriorityMiniChart(priorityDistribution) {
    var chartEl = document.getElementById("insight-priority-chart");
    if (!chartEl || !window.echarts) {
        return;
    }

    var chartData = [];
    Object.keys(priorityDistribution || {}).forEach(function (key) {
        chartData.push({ name: key, value: priorityDistribution[key] });
    });

    priorityChartInstance = getChartInstance(chartEl, priorityChartInstance);
    if (!priorityChartInstance) {
        return;
    }

    priorityChartInstance.setOption({
        tooltip: { trigger: "item" },
        legend: { bottom: 0, icon: "circle" },
        series: [
            {
                type: "pie",
                radius: ["42%", "72%"],
                itemStyle: { borderRadius: 6, borderColor: "#fff", borderWidth: 2 },
                data: chartData,
            },
        ],
    });

    bindChartResize();
}

function renderTimelineMiniChart(timelineItems) {
    var chartEl = document.getElementById("insight-timeline-chart");
    if (!chartEl || !window.echarts) {
        return;
    }

    var xAxisData = [];
    var yAxisData = [];
    (timelineItems || []).forEach(function (item) {
        xAxisData.push(item.date.slice(5));
        yAxisData.push(item.count);
    });

    timelineChartInstance = getChartInstance(chartEl, timelineChartInstance);
    if (!timelineChartInstance) {
        return;
    }

    timelineChartInstance.setOption({
        tooltip: { trigger: "axis" },
        grid: { left: 30, right: 16, top: 20, bottom: 30 },
        xAxis: {
            type: "category",
            data: xAxisData,
            axisLabel: { fontSize: 10 },
        },
        yAxis: {
            type: "value",
            minInterval: 1,
        },
        series: [
            {
                type: "line",
                smooth: true,
                data: yAxisData,
                areaStyle: { opacity: 0.15 },
                lineStyle: { width: 3 },
                symbolSize: 8,
            },
        ],
    });

    bindChartResize();
}

function loadInsightsBoard(board, userId) {
    if (isInsightsLoading) {
        return;
    }

    var statusLabel = document.getElementById("insight-status");
    var refreshBtn = document.getElementById("insight-refresh");

    isInsightsLoading = true;
    board.classList.add("is-loading");
    if (refreshBtn) {
        refreshBtn.disabled = true;
    }

    if (statusLabel) {
        statusLabel.textContent = "Computing performance intelligence...";
    }

    var insightsUrl = "/api/insights";
    var timelineUrl = "/api/timeline?days=14";
    var summaryUrl = "/api/summary";

    Promise.all([fetch(insightsUrl), fetch(timelineUrl), fetch(summaryUrl)])
        .then(function (responses) {
            return Promise.all(
                responses.map(function (response) {
                    return response.json().then(function (payload) {
                        if (!response.ok) {
                            throw new Error(resolveApiErrorMessage(response, payload));
                        }
                        return payload;
                    });
                })
            );
        })
        .then(function (payloads) {
            var insights = payloads[0];
            var timeline = payloads[1];
            var summary = payloads[2];
            var kpis = insights.kpis || {};
            var effectiveCompletionRate = Number(kpis.completion_rate || summary.progress_rate || 0);

            if (kpis.completion_rate === undefined || kpis.completion_rate === null) {
                kpis.completion_rate = effectiveCompletionRate;
            }

            setMetricValue("insight-productivity", Number(kpis.productivity_score || 0).toFixed(2));
            setMetricValue("insight-stability", Number(kpis.stability_rate || 0).toFixed(2), "%");
            setMetricValue("insight-urgent", kpis.urgent_open || 0);
            setMetricValue("insight-upcoming", kpis.upcoming_7_days || 0);

            renderPriorityMiniChart(insights.priority_distribution || {});
            renderTimelineMiniChart(timeline.timeline || []);
            renderTrendStrip(timeline.timeline || []);
            renderHeatmap(timeline.timeline || []);
            setFocusRecommendations(kpis);
            setRiskAlerts(kpis);
            setInsightSummary(kpis);
            setHealthBadge(kpis);
            renderModuleSpotlight(insights.module_distribution || {}, insights.module_hotspots || []);

            if (statusLabel) {
                statusLabel.textContent = "Live metrics synced successfully.";
            }
            setInsightSyncStampFromPayload(summary.generated_at, insights.generated_at || timeline.generated_at);
        })
        .catch(function (error) {
            setHealthBadge({ completion_rate: 0, overdue_rate: 100 });
            setRiskAlerts({ urgent_open: 0, overdue_rate: 100, completion_rate: 0, upcoming_7_days: 0 });
            setInsightSummary({ completion_rate: 0, urgent_open: 0, overdue_rate: 100 });
            if (statusLabel) {
                var message = (error && error.message) ? error.message : "Unable to load live metrics right now.";
                statusLabel.textContent = "Unable to load live metrics right now. " + message;
            }
            setInsightSyncStamp(false);
        })
        .finally(function () {
            isInsightsLoading = false;
            board.classList.remove("is-loading");
            if (refreshBtn) {
                refreshBtn.disabled = false;
            }
        });
}

function initInsightsBoard() {
    var board = document.querySelector("[data-insight-board]");
    if (!board) {
        return;
    }

    var userId = board.getAttribute("data-user-id");
    if (!userId) {
        return;
    }

    var refreshBtn = document.getElementById("insight-refresh");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", function () {
            loadInsightsBoard(board, userId);
        });
    }

    loadInsightsBoard(board, userId);
}

document.addEventListener("DOMContentLoaded", function () {
    setNowForTaskInputs();
    bindCreateTaskValidation();
    bindToastActions();
    bindPopovers();
    initInsightsBoard();
    renderRelativeDeadlines();
    autoHideAlertToasts();
});

// ── Relative deadline display ────────────────────────────────────
function renderRelativeDeadlines() {
    var elements = document.querySelectorAll(".deadline-display[data-deadline]");
    var now = new Date();
    elements.forEach(function (el) {
        var iso = el.getAttribute("data-deadline");
        if (!iso) return;
        var dt = new Date(iso);
        if (isNaN(dt.getTime())) return;

        var diffMs = dt - now;
        var diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
        var label;

        if (diffMs < 0) {
            var overDays = Math.abs(Math.floor(diffMs / (1000 * 60 * 60 * 24)));
            label = overDays === 0 ? "Overdue today" : "Overdue by " + overDays + "d";
            el.classList.add("deadline-overdue");
        } else if (diffDays <= 3) {
            label = diffDays === 0 ? "Due today" : "In " + diffDays + " day" + (diffDays > 1 ? "s" : "");
            el.classList.add("deadline-soon");
        } else {
            label = "In " + diffDays + " days";
            el.classList.add("deadline-ok");
        }

        el.setAttribute("title", el.textContent.trim());
        el.textContent = label;
    });
}

// ── Auto-hide alert toasts after 6 seconds ───────────────────────
function autoHideAlertToasts() {
    var toasts = document.querySelectorAll(".alert-toast");
    toasts.forEach(function (toast) {
        setTimeout(function () {
            toast.style.transition = "opacity 0.6s ease";
            toast.style.opacity = "0";
            setTimeout(function () { toast.remove(); }, 650);
        }, 6000);
    });
}

// ── Update insight API calls to use session (no user_id param) ──
var insightsUrl = "/api/insights";
var timelineUrl = "/api/timeline?days=14";


