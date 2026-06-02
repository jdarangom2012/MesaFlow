(() => {
    const TYPE_CONFIG = {
        success: { icon: "\u2713", duration: 3000, label: "Exito" },
        info: { icon: "i", duration: 4000, label: "Informacion" },
        warning: { icon: "!", duration: 5000, label: "Atencion" },
        error: { icon: "\u00d7", duration: 6000, label: "Error" },
    };

    const ensureContainer = () => {
        let container = document.getElementById("toast-container");

        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.className = "mf-toast-container";
            container.setAttribute("aria-live", "polite");
            container.setAttribute("aria-atomic", "false");
            document.body.appendChild(container);
        }

        return container;
    };

    const removeToast = (toast) => {
        if (!toast || toast.dataset.removing === "true") {
            return;
        }

        toast.dataset.removing = "true";
        window.clearTimeout(Number(toast.dataset.timerId || 0));
        toast.classList.add("is-leaving");
        window.setTimeout(() => toast.remove(), 220);
    };

    const createToast = (message, type = "info", options = {}) => {
        const normalizedType = TYPE_CONFIG[type] ? type : "info";
        const config = TYPE_CONFIG[normalizedType];
        const toast = document.createElement("section");
        toast.className = `mf-toast mf-toast-${normalizedType}`;
        toast.setAttribute("role", normalizedType === "error" ? "alert" : "status");
        toast.innerHTML = `
            <span class="mf-toast-icon" aria-hidden="true">${config.icon}</span>
            <span class="mf-toast-copy">
                <span class="mf-toast-label">${config.label}</span>
                <span class="mf-toast-message"></span>
            </span>
            <button class="mf-toast-close" type="button" aria-label="Cerrar notificacion">&times;</button>
        `;
        toast.querySelector(".mf-toast-message").textContent = String(message || "");
        toast.querySelector(".mf-toast-close").addEventListener("click", () => removeToast(toast));

        const duration = options.duration === 0 ? 0 : (options.duration || config.duration);

        if (duration > 0) {
            toast.dataset.timerId = String(window.setTimeout(() => removeToast(toast), duration));
        }

        return toast;
    };

    window.showToast = (message, type = "info", options = {}) => {
        const container = ensureContainer();
        const toast = createToast(message, type, options);
        const maxVisibleToasts = window.matchMedia("(max-width: 620px)").matches ? 3 : 5;
        container.appendChild(toast);

        while (container.children.length > maxVisibleToasts) {
            const oldestToast = container.firstElementChild;
            window.clearTimeout(Number(oldestToast.dataset.timerId || 0));
            oldestToast.remove();
        }

        requestAnimationFrame(() => toast.classList.add("is-visible"));
        return toast;
    };

    window.showToastConfirm = (message, options = {}) => new Promise((resolve) => {
        const container = ensureContainer();
        const toast = createToast(message, options.type || "warning", { duration: 0 });
        const actions = document.createElement("span");
        actions.className = "mf-toast-actions";
        actions.innerHTML = `
            <button class="mf-toast-action mf-toast-action-secondary" type="button">Cancelar</button>
            <button class="mf-toast-action mf-toast-action-primary" type="button">Confirmar</button>
        `;
        toast.querySelector(".mf-toast-copy").appendChild(actions);
        const finish = (accepted) => {
            removeToast(toast);
            resolve(accepted);
        };
        actions.children[0].addEventListener("click", () => finish(false));
        actions.children[1].addEventListener("click", () => finish(true));
        toast.querySelector(".mf-toast-close").addEventListener("click", () => resolve(false), { once: true });
        container.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add("is-visible"));
    });

    document.addEventListener("DOMContentLoaded", () => {
        ensureContainer();
        document.querySelectorAll("[data-toast-message]").forEach((node) => {
            window.showToast(node.dataset.toastMessage || node.textContent.trim(), node.dataset.toastType || "info");
            node.hidden = true;
        });
    });
})();
