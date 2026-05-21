(function () {
    var storageKey = "portfolio_theme";

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        try {
            localStorage.setItem(storageKey, theme);
        } catch (err) {
            // Ignore storage errors in restricted environments.
        }
    }

    function getInitialTheme() {
        try {
            var stored = localStorage.getItem(storageKey);
            if (stored === "dark" || stored === "light") {
                return stored;
            }
        } catch (err) {
            // Ignore storage errors in restricted environments.
        }

        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return "dark";
        }
        return "light";
    }

    function syncButtonLabel(button, theme) {
        if (!button) {
            return;
        }
        button.textContent = theme === "dark" ? "Switch to Light" : "Switch to Dark";
    }

    document.addEventListener("DOMContentLoaded", function () {
        var theme = getInitialTheme();
        applyTheme(theme);

        var toggle = document.getElementById("theme-toggle");
        syncButtonLabel(toggle, theme);

        if (toggle) {
            toggle.addEventListener("click", function () {
                var current = document.documentElement.getAttribute("data-theme") || "light";
                var next = current === "dark" ? "light" : "dark";
                applyTheme(next);
                syncButtonLabel(toggle, next);
            });
        }
    });
})();
