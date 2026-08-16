(() => {
    "use strict";

    const button = document.querySelector("#sidebar-toggle");
    const backdrop = document.querySelector("#sidebar-backdrop");

    function setOpen(open) {
        document.body.classList.toggle("sidebar-open", open);
        button?.setAttribute("aria-expanded", String(open));
    }

    button?.addEventListener("click", () => {
        const sidebarIsOpen = document.body.classList.contains("sidebar-open");
        setOpen(!sidebarIsOpen);
    });

    backdrop?.addEventListener("click", () => {
        setOpen(false);
    });

    window.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            setOpen(false);
        }
    });
})();
