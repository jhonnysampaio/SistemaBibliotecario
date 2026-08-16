(() => {
    "use strict";

    const storageKey = "biblioteca-tema";
    const button = document.querySelector("#theme-toggle");
    const icon = button?.querySelector("i");
    const savedTheme = localStorage.getItem(storageKey);

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;

        const darkThemeIsActive = theme === "dark";
        button?.setAttribute("aria-pressed", String(darkThemeIsActive));

        if (icon) {
            icon.className = darkThemeIsActive
                ? "bi bi-sun"
                : "bi bi-moon-stars";
        }
    }

    if (savedTheme === "dark" || savedTheme === "light") {
        applyTheme(savedTheme);
    }

    button?.addEventListener("click", () => {
        const nextTheme = document.documentElement.dataset.theme === "dark"
            ? "light"
            : "dark";

        applyTheme(nextTheme);
        localStorage.setItem(storageKey, nextTheme);
    });
})();
