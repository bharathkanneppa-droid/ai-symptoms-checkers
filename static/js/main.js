/* MediAssist AI - global frontend behaviour */
(function () {
    "use strict";

    // ---------------------------------------------------------------
    // Dark mode (persisted in localStorage, applied via data-bs-theme)
    // ---------------------------------------------------------------
    const THEME_KEY = "medassist-theme";

    function getSavedTheme() {
        try { return localStorage.getItem(THEME_KEY) || "light"; } catch (e) { return "light"; }
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-bs-theme", theme);
        try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* ignore */ }
        document.querySelectorAll("#themeToggle i").forEach(function (icon) {
            icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
        });
    }

    applyTheme(getSavedTheme());

    document.addEventListener("click", function (event) {
        if (event.target.closest("#themeToggle")) {
            const next = document.documentElement.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
            applyTheme(next);
        }
    });

    // ---------------------------------------------------------------
    // Mobile sidebar toggle
    // ---------------------------------------------------------------
    const sidebar = document.getElementById("appSidebar");
    const toggle = document.getElementById("sidebarToggle");
    if (sidebar && toggle) {
        toggle.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });
        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", function (event) {
            if (window.innerWidth <= 992 && sidebar.classList.contains("show")) {
                if (!sidebar.contains(event.target) && !toggle.contains(event.target)) {
                    sidebar.classList.remove("show");
                }
            }
        });
    }

    // ---------------------------------------------------------------
    // Auto-dismiss alerts after a few seconds
    // ---------------------------------------------------------------
    document.querySelectorAll(".alert-dismissible").forEach(function (alert) {
        setTimeout(function () {
            const close = alert.querySelector(".btn-close");
            if (close) close.click();
        }, 6000);
    });

    // ---------------------------------------------------------------
    // Flash messages as Bootstrap toasts
    // ---------------------------------------------------------------
    document.querySelectorAll("#toastContainer .toast").forEach(function (toast) {
        if (window.bootstrap) new bootstrap.Toast(toast, { delay: 5000 }).show();
    });
})();
