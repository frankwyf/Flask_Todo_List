(function () {
    const shellSelector = '[data-chart-shell]';
    const hintSelector = '[data-chart-hint]';
    const dismissSelector = '[data-chart-hint-dismiss]';
    const storageKey = 'chartHintDismissed';

    function isNarrowScreen() {
        return window.matchMedia('(max-width: 760px)').matches;
    }

    function updateShellEdge(shell) {
        const nearEnd = shell.scrollLeft + shell.clientWidth >= shell.scrollWidth - 8;
        shell.classList.toggle('is-scroll-end', nearEnd);
    }

    function bindChartShellBehavior(shell) {
        shell.addEventListener('scroll', function () {
            updateShellEdge(shell);
        }, { passive: true });

        shell.addEventListener('keydown', function (event) {
            if (event.key === 'ArrowRight') {
                shell.scrollBy({ left: 120, behavior: 'smooth' });
                event.preventDefault();
            }
            if (event.key === 'ArrowLeft') {
                shell.scrollBy({ left: -120, behavior: 'smooth' });
                event.preventDefault();
            }
        });

        updateShellEdge(shell);
    }

    function syncHintVisibility() {
        const dismissed = localStorage.getItem(storageKey) === '1';
        const hints = document.querySelectorAll(hintSelector);
        hints.forEach(function (hint) {
            const hidden = dismissed || !isNarrowScreen();
            hint.classList.toggle('is-hidden', hidden);
            hint.setAttribute('aria-hidden', hidden ? 'true' : 'false');
        });
    }

    function bindHintDismiss() {
        const dismissButtons = document.querySelectorAll(dismissSelector);
        dismissButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                localStorage.setItem(storageKey, '1');
                syncHintVisibility();
            });
        });
    }

    function bindEscapeToDismiss() {
        document.addEventListener('keydown', function (event) {
            if (event.key !== 'Escape') {
                return;
            }
            localStorage.setItem(storageKey, '1');
            syncHintVisibility();
        });
    }

    function init() {
        const shells = document.querySelectorAll(shellSelector);
        if (!shells.length) {
            return;
        }

        shells.forEach(bindChartShellBehavior);
        bindHintDismiss();
        bindEscapeToDismiss();
        syncHintVisibility();

        window.addEventListener('resize', syncHintVisibility);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
