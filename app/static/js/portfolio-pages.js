(function () {
    function bindEndpointFilter() {
        var filterInput = document.getElementById("endpoint-filter");
        var cards = Array.prototype.slice.call(document.querySelectorAll("[data-endpoint-card]"));
        var counter = document.getElementById("filter-count");

        if (!filterInput || !cards.length) {
            return;
        }

        function applyFilter() {
            var query = (filterInput.value || "").toLowerCase().trim();
            var visible = 0;

            cards.forEach(function (card) {
                var text = (card.textContent || "").toLowerCase();
                var show = !query || text.indexOf(query) >= 0;
                card.classList.toggle("is-hidden", !show);
                if (show) {
                    visible += 1;
                }
            });

            if (counter) {
                counter.textContent = visible + " endpoint(s) visible";
            }
        }

        filterInput.addEventListener("input", applyFilter);
        applyFilter();
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
                    copyPromise = navigator.clipboard.writeText(value);
                } else {
                    copyPromise = Promise.reject(new Error("Clipboard API unavailable"));
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
        bindEndpointFilter();
        bindCopyButtons();
        bindRevealAnimation();
    });
})();
