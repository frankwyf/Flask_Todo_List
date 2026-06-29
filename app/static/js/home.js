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

function renderModuleSpotlight(moduleDistribution) {
    var list = document.getElementById("insight-module-list");
    if (!list) {
        return;
    }

    var rows = Object.keys(moduleDistribution || {}).map(function (name) {
        return { name: name, count: Number(moduleDistribution[name] || 0) };
    });
    rows.sort(function (a, b) {
        return b.count - a.count;
    });

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

    var insightsUrl = "/api/insights?user_id=" + encodeURIComponent(userId);
    var timelineUrl = "/api/timeline?user_id=" + encodeURIComponent(userId) + "&days=14";

    Promise.all([fetch(insightsUrl), fetch(timelineUrl)])
        .then(function (responses) {
            return Promise.all(
                responses.map(function (response) {
                    if (!response.ok) {
                        throw new Error("Failed to load dashboard insights.");
                    }
                    return response.json();
                })
            );
        })
        .then(function (payloads) {
            var insights = payloads[0];
            var timeline = payloads[1];
            var kpis = insights.kpis || {};

            setMetricValue("insight-productivity", Number(kpis.productivity_score || 0).toFixed(2));
            setMetricValue("insight-stability", Number(kpis.stability_rate || 0).toFixed(2), "%");
            setMetricValue("insight-urgent", kpis.urgent_open || 0);
            setMetricValue("insight-upcoming", kpis.upcoming_7_days || 0);

            renderPriorityMiniChart(insights.priority_distribution || {});
            renderTimelineMiniChart(timeline.timeline || []);
            renderTrendStrip(timeline.timeline || []);
            renderHeatmap(timeline.timeline || []);
            setFocusRecommendations(kpis);
            setHealthBadge(kpis);
            renderModuleSpotlight(insights.module_distribution || {});

            if (statusLabel) {
                statusLabel.textContent = "Live metrics synced successfully.";
            }
        })
        .catch(function () {
            setHealthBadge({ completion_rate: 0, overdue_rate: 100 });
            if (statusLabel) {
                statusLabel.textContent = "Unable to load live metrics right now.";
            }
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
});


