(function () {
    var cards = [];
    var activeCategory = "all";
    var activeQuery = "";
    var expanded = false;

    function fallbackCopyText(value) {
        var temp = document.createElement("textarea");
        temp.value = value;
        temp.setAttribute("readonly", "readonly");
        temp.style.position = "fixed";
        temp.style.top = "-9999px";
        document.body.appendChild(temp);
        temp.focus();
        temp.select();
        var copied = false;

        try {
            copied = document.execCommand("copy");
        } catch (_error) {
            copied = false;
        }

        document.body.removeChild(temp);
        return copied;
    }

    function getCounterElement() {
        return document.getElementById("filter-count");
    }

    function updateMetrics() {
        if (!cards.length) {
            return;
        }

        var totalElement = document.getElementById("metric-total");
        var apiElement = document.getElementById("metric-api");
        var workflowElement = document.getElementById("metric-workflow");
        var chartElement = document.getElementById("metric-chart");

        var apiCount = cards.filter(function (card) {
            return card.getAttribute("data-category") === "api";
        }).length;

        var workflowCount = cards.filter(function (card) {
            var category = card.getAttribute("data-category") || "";
            return category === "task" || category === "search";
        }).length;

        var chartCount = cards.filter(function (card) {
            return card.getAttribute("data-category") === "chart";
        }).length;

        if (totalElement) {
            totalElement.textContent = String(cards.length);
        }
        if (apiElement) {
            apiElement.textContent = String(apiCount);
        }
        if (workflowElement) {
            workflowElement.textContent = String(workflowCount);
        }
        if (chartElement) {
            chartElement.textContent = String(chartCount);
        }
    }

    function applyFilters() {
        var visible = 0;

        cards.forEach(function (card) {
            var text = (card.textContent || "").toLowerCase();
            var category = (card.getAttribute("data-category") || "").toLowerCase();
            var matchesQuery = !activeQuery || text.indexOf(activeQuery) >= 0;
            var matchesCategory = activeCategory === "all" || category === activeCategory;
            var show = matchesQuery && matchesCategory;

            card.classList.toggle("is-hidden", !show);
            if (show) {
                visible += 1;
            }
        });

        var counter = getCounterElement();
        if (counter) {
            counter.textContent = visible + " endpoint(s) visible";
        }
    }

    function setExpandedState(isExpanded) {
        expanded = isExpanded;
        cards.forEach(function (card) {
            card.classList.toggle("is-expanded", expanded);
        });

        var expandBtn = document.getElementById("endpoint-expand");
        if (expandBtn) {
            expandBtn.textContent = expanded ? "Collapse All" : "Expand All";
            expandBtn.setAttribute("aria-pressed", expanded ? "true" : "false");
        }
    }

    function bindEndpointFilter() {
        var filterInput = document.getElementById("endpoint-filter");
        var clearBtn = document.getElementById("endpoint-clear");
        if (!filterInput || !cards.length) {
            return;
        }

        filterInput.addEventListener("input", function () {
            activeQuery = (filterInput.value || "").toLowerCase().trim();
            applyFilters();
        });

        document.addEventListener("keydown", function (event) {
            if (event.key !== "/") {
                if (event.key === "Escape") {
                    activeQuery = "";
                    activeCategory = "all";
                    filterInput.value = "";
                    var categoryButtons = document.querySelectorAll("[data-filter-category]");
                    categoryButtons.forEach(function (btn) {
                        var isAll = (btn.getAttribute("data-filter-category") || "") === "all";
                        btn.classList.toggle("is-active", isAll);
                        btn.setAttribute("aria-pressed", isAll ? "true" : "false");
                    });
                    applyFilters();
                }
                return;
            }

            var target = event.target;
            var isTypingContext = target && (
                target.tagName === "INPUT" ||
                target.tagName === "TEXTAREA" ||
                target.tagName === "SELECT" ||
                target.isContentEditable
            );

            if (!isTypingContext) {
                event.preventDefault();
                filterInput.focus();
                filterInput.select();
            }
        });

        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                filterInput.value = "";
                activeQuery = "";
                activeCategory = "all";
                var categoryButtons = document.querySelectorAll("[data-filter-category]");
                categoryButtons.forEach(function (btn) {
                    var isAll = (btn.getAttribute("data-filter-category") || "") === "all";
                    btn.classList.toggle("is-active", isAll);
                    btn.setAttribute("aria-pressed", isAll ? "true" : "false");
                });
                applyFilters();
                filterInput.focus();
            });
        }
    }

    function bindCategoryFilter() {
        var categoryButtons = document.querySelectorAll("[data-filter-category]");
        if (!categoryButtons.length) {
            return;
        }

        categoryButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                activeCategory = (button.getAttribute("data-filter-category") || "all").toLowerCase();
                categoryButtons.forEach(function (btn) {
                    var isActive = btn === button;
                    btn.classList.toggle("is-active", isActive);
                    btn.setAttribute("aria-pressed", isActive ? "true" : "false");
                });
                applyFilters();
            });
        });
    }

    function bindCopyButtons() {
        var buttons = document.querySelectorAll("[data-copy-value]");
        if (!buttons.length) {
            return;
        }

        buttons.forEach(function (button) {
            var initialText = button.textContent;
            button.addEventListener("click", function () {
                var value = button.getAttribute("data-copy-value") || "";
                if (!value) {
                    return;
                }

                var copyPromise;
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    copyPromise = navigator.clipboard.writeText(value).catch(function () {
                        if (!fallbackCopyText(value)) {
                            throw new Error("Copy failed");
                        }
                    });
                } else {
                    copyPromise = fallbackCopyText(value)
                        ? Promise.resolve()
                        : Promise.reject(new Error("Clipboard unavailable"));
                }

                copyPromise
                    .then(function () {
                        button.textContent = "Copied";
                        window.setTimeout(function () {
                            button.textContent = initialText;
                        }, 900);
                    })
                    .catch(function () {
                        button.textContent = "Copy failed";
                        window.setTimeout(function () {
                            button.textContent = initialText;
                        }, 1200);
                    });
            });
        });
    }

    function bindExpandToggle() {
        var button = document.getElementById("endpoint-expand");
        if (!button) {
            return;
        }

        button.addEventListener("click", function () {
            setExpandedState(!expanded);
        });
    }

    function bindCardExpand() {
        cards.forEach(function (card) {
            card.addEventListener("click", function (event) {
                if (event.target && event.target.closest("button")) {
                    return;
                }
                card.classList.toggle("is-expanded");
            });
        });
    }

    function bindRevealAnimation() {
        var elements = document.querySelectorAll(".reveal");
        if (!elements.length || !window.IntersectionObserver) {
            elements.forEach(function (el) {
                el.classList.add("is-visible");
            });
            return;
        }

        var observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.12 }
        );

        elements.forEach(function (el) {
            observer.observe(el);
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        cards = Array.prototype.slice.call(document.querySelectorAll("[data-endpoint-card]"));
        updateMetrics();
        bindEndpointFilter();
        bindCategoryFilter();
        bindCopyButtons();
        bindExpandToggle();
        bindCardExpand();
        bindRevealAnimation();
        applyFilters();
        setExpandedState(false);
    });
})();
