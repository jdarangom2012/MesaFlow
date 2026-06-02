document.addEventListener("DOMContentLoaded", () => {
    const IVA_RATE = 0.19;
    const cart = new Map();
    let selectedPaymentMethod = "CASH";
    let selectedTable = null;
    let activeOrder = null;
    let lastPaidOrderId = null;
    let selectedCategoryId = "";
    let elapsedTimerId = null;

    const addButtons = document.querySelectorAll(".pos-add-product");
    const cartItems = document.getElementById("pos-cart-items");
    const cartCount = document.getElementById("pos-cart-count");
    const subtotalNode = document.getElementById("pos-subtotal");
    const taxNode = document.getElementById("pos-tax");
    const tipNode = document.getElementById("pos-tip");
    const totalNode = document.getElementById("pos-total");
    const sendOrderButton = document.getElementById("pos-send-order-button");
    const checkoutButton = document.getElementById("pos-checkout-button");
    const selectedTableNode = document.getElementById("pos-selected-table");
    const selectedTableTopNode = document.getElementById("pos-current-table-top");
    const selectedPeopleNode = document.getElementById("pos-current-people");
    const selectedTimeNode = document.getElementById("pos-current-time");
    const posRoot = document.querySelector("[data-create-order-url]");
    const tableOptions = document.querySelectorAll(".pos-table-option");
    const productSearchInput = document.getElementById("pos-product-search");
    const productCards = document.querySelectorAll(".pos-product-card");
    const categoryFilters = document.querySelectorAll(".pos-category-filter");
    const paymentModal = document.getElementById("pos-payment-modal");
    const paymentClose = document.getElementById("pos-payment-close");
    const paymentOrderLabel = document.getElementById("pos-payment-order-label");
    const confirmPaymentButton = document.getElementById("pos-confirm-payment");
    const paymentMethodButtons = document.querySelectorAll("[data-payment-method]:not(.pos-modal-method)");
    const modalMethodButtons = document.querySelectorAll(".pos-modal-method");
    const modalSubtotalNode = document.getElementById("pos-modal-subtotal");
    const modalTaxNode = document.getElementById("pos-modal-tax");
    const modalTotalNode = document.getElementById("pos-modal-total");
    const printActions = document.getElementById("pos-print-actions");
    const printTicketButton = document.getElementById("pos-print-ticket");
    const printKitchenButton = document.getElementById("pos-print-kitchen");
    const tableRequiredModal = document.getElementById("pos-table-required-modal");
    const tableRequiredClose = document.getElementById("pos-table-required-close");

    if (!cartItems || !cartCount || !subtotalNode || !taxNode || !tipNode || !totalNode || !posRoot) {
        return;
    }

    const moneyFormatter = new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0,
    });

    const formatMoney = (value) => moneyFormatter.format(value);

    const openPrintWindow = (url) => {
        if (!url) {
            return;
        }

        const popup = window.open(url, "_blank", "noopener,width=420,height=720");

        if (!popup) {
            window.showToast("El navegador bloqueó la impresión automática. Permite popups para MesaFlow.", "warning");
        }
    };

    const pulseNode = (node) => {
        if (!node) {
            return;
        }

        node.classList.remove("pos-order-pulse");
        void node.offsetWidth;
        node.classList.add("pos-order-pulse");
    };

    const pulseOrderSummary = () => {
        [cartCount, subtotalNode, taxNode, totalNode].forEach(pulseNode);
    };

    const getCsrfToken = () => {
        const tokenInput = document.querySelector("[name=csrfmiddlewaretoken]");

        if (tokenInput) {
            return tokenInput.value;
        }

        return document.cookie
            .split(";")
            .map((cookie) => cookie.trim())
            .find((cookie) => cookie.startsWith("csrftoken="))
            ?.split("=")[1] || "";
    };

    const escapeHtml = (value) => {
        const node = document.createElement("div");
        node.textContent = value || "";
        return node.innerHTML;
    };

    const getCartTotals = () => {
        const subtotal = Array.from(cart.values()).reduce((sum, item) => {
            return sum + item.price * item.quantity;
        }, 0);
        const tax = subtotal * IVA_RATE;
        const tip = 0;

        return {
            subtotal,
            tax,
            tip,
            total: subtotal + tax + tip,
            itemCount: Array.from(cart.values()).reduce((sum, item) => sum + item.quantity, 0),
        };
    };

    const getTemplateUrl = (template, id) => template.replace(/\/0(?=\/)/, `/${id}`);

    const formatElapsedTime = (startedAt) => {
        if (!startedAt) {
            return "--:--";
        }

        const started = new Date(startedAt);

        if (Number.isNaN(started.getTime())) {
            return "--:--";
        }

        const elapsedSeconds = Math.max(Math.floor((Date.now() - started.getTime()) / 1000), 0);
        const hours = Math.floor(elapsedSeconds / 3600);
        const minutes = Math.floor((elapsedSeconds % 3600) / 60);

        return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
    };

    const stopElapsedTimer = () => {
        if (elapsedTimerId) {
            window.clearInterval(elapsedTimerId);
            elapsedTimerId = null;
        }
    };

    const updateElapsedBadge = () => {
        if (!selectedTimeNode) {
            return;
        }

        selectedTimeNode.textContent = activeOrder?.created_at ? formatElapsedTime(activeOrder.created_at) : "--:--";
    };

    const startElapsedTimer = () => {
        stopElapsedTimer();
        updateElapsedBadge();

        if (activeOrder?.created_at) {
            elapsedTimerId = window.setInterval(updateElapsedBadge, 1000);
        }
    };

    const readJsonResponse = async (response, fallbackMessage) => {
        const contentType = response.headers.get("content-type") || "";

        if (contentType.includes("application/json")) {
            return response.json();
        }

        if (response.status === 401 || response.redirected) {
            throw new Error("Tu sesión expiró. Inicia sesión nuevamente.");
        }

        if (response.status === 403) {
            throw new Error("Tu usuario no tiene permiso para realizar esta acción.");
        }

        throw new Error(fallbackMessage);
    };

    const showTableRequiredModal = () => {
        if (!tableRequiredModal) {
            window.showToast("Selecciona una mesa antes de continuar.", "warning");
            return;
        }

        tableRequiredModal.hidden = false;
        tableRequiredModal.style.display = "flex";
    };

    const closeTableRequiredModal = () => {
        if (!tableRequiredModal) {
            return;
        }

        tableRequiredModal.hidden = true;
        tableRequiredModal.style.display = "none";
    };

    const setSelectedPaymentMethod = (method) => {
        selectedPaymentMethod = method || "CASH";

        modalMethodButtons.forEach((button) => {
            const isSelected = button.dataset.paymentMethod === selectedPaymentMethod;
            button.style.background = isSelected ? "#00D4FF" : "#111C2D";
            button.style.color = isSelected ? "#07111F" : "white";
            button.style.borderColor = isSelected ? "rgba(0,212,255,.24)" : "rgba(255,255,255,.08)";
        });
    };

    const updateCheckoutState = () => {
        if (!checkoutButton) {
            return;
        }

        const canPay = activeOrder?.status === "READY";
        checkoutButton.disabled = !canPay;
        checkoutButton.style.opacity = canPay ? "1" : ".45";
        checkoutButton.style.cursor = canPay ? "pointer" : "not-allowed";
        checkoutButton.textContent = canPay ? `COBRAR ORDEN #${activeOrder.order_id}` : "COBRAR ORDEN LISTA";
    };

    const updateSelectedTableLabel = () => {
        const setLabel = (value) => {
            if (selectedTableNode) {
                selectedTableNode.textContent = value;
            }
            if (selectedTableTopNode) {
                selectedTableTopNode.textContent = value;
            }
        };

        if (!selectedTable) {
            setLabel("Seleccione una mesa");
            if (selectedPeopleNode) {
                selectedPeopleNode.textContent = "-- Personas";
            }
            activeOrder = null;
            startElapsedTimer();
            return;
        }

        if (selectedPeopleNode) {
            const capacity = selectedTable.capacity || "--";
            selectedPeopleNode.textContent = `${capacity} Personas`;
        }
        startElapsedTimer();

        if (activeOrder) {
            setLabel(`Mesa: ${selectedTable.name} · Orden #${activeOrder.order_id}`);
            return;
        }

        setLabel(`Mesa: ${selectedTable.name}`);
    };

    const updateTableVisual = (tableId, status, label, order = null) => {
        const tableOption = document.querySelector(`.pos-table-option[data-table-id="${tableId}"]`);

        if (!tableOption) {
            return;
        }

        tableOption.dataset.tableStatus = status;
        tableOption.dataset.activeOrderId = order?.order_id || "";
        tableOption.dataset.activeOrderStatus = order?.status || "";
        tableOption.dataset.activeOrderTotal = order?.total || "";
        tableOption.dataset.activeOrderCreatedAt = order?.created_at || "";
        const visualStatus = order?.status || status;
        const styles = {
            FREE: ["rgba(0,255,198,.08)", "rgba(0,255,198,.24)", "#00FFC6"],
            OPEN: ["rgba(0,212,255,.12)", "rgba(0,212,255,.30)", "#00D4FF"],
            OCCUPIED: ["rgba(0,212,255,.12)", "rgba(0,212,255,.30)", "#00D4FF"],
            PREPARING: ["rgba(255,193,7,.12)", "rgba(255,193,7,.32)", "#FFC107"],
            READY: ["rgba(0,255,198,.14)", "rgba(0,255,198,.38)", "#00FFC6"],
            PAID: ["rgba(143,167,192,.10)", "rgba(143,167,192,.20)", "#8FA7C0"],
        };
        const [background, border, color] = styles[visualStatus] || styles.OCCUPIED;
        tableOption.style.background = background;
        tableOption.style.borderColor = border;
        tableOption.style.color = color;
        const statusLabel = tableOption.querySelector("[data-table-status-label]");
        if (statusLabel) {
            statusLabel.textContent = label;
        }
    };

    const syncActiveOrderFromDataset = (tableOption) => {
        if (!tableOption.dataset.activeOrderId) {
            activeOrder = null;
            return;
        }

        activeOrder = {
            order_id: Number(tableOption.dataset.activeOrderId),
            status: tableOption.dataset.activeOrderStatus,
            status_label: tableOption.querySelector("[data-table-status-label]")?.textContent?.trim() || tableOption.dataset.activeOrderStatus,
            total: Number.parseFloat(tableOption.dataset.activeOrderTotal || "0"),
            created_at: tableOption.dataset.activeOrderCreatedAt || "",
            table_id: Number(tableOption.dataset.tableId),
            table_name: tableOption.dataset.tableName,
            table_capacity: Number(tableOption.dataset.tableCapacity || "0"),
        };
    };

    const fetchActiveOrder = async (tableId) => {
        const activeOrderUrl = getTemplateUrl(posRoot.dataset.activeOrderUrlTemplate, tableId);
        const response = await fetch(activeOrderUrl);
        const data = await readJsonResponse(response, "No se pudo consultar la mesa seleccionada.");

        if (!response.ok || !data.success) {
            throw new Error(data.error || "No se pudo consultar la orden activa.");
        }

        if (data.has_order) {
            activeOrder = data;
            updateTableVisual(tableId, "OCCUPIED", data.status_label, data);
        } else {
            activeOrder = null;
            updateTableVisual(tableId, data.table_status, data.table_status === "FREE" ? "Libre" : data.table_status);
        }

        updateSelectedTableLabel();
        updateCheckoutState();
    };

    const createCartItem = (item) => {
        const wrapper = document.createElement("div");
        wrapper.className = "pos-order-item";

        wrapper.innerHTML = `
            <div style="display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:start;">
                <div style="min-width:0;">
                    <div style="font-size:15px;font-weight:850;color:white;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                        ${escapeHtml(item.name)}
                    </div>
                    <div style="color:#8FA7C0;font-size:12px;margin-top:4px;">
                        ${item.quantity} x ${formatMoney(item.price)}
                    </div>
                </div>
                <div style="color:#00D4FF;font-weight:900;font-size:16px;white-space:nowrap;text-align:right;">
                    ${formatMoney(item.price * item.quantity)}
                </div>
            </div>

            <div style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;gap:10px;">
                <div style="display:flex;align-items:center;gap:8px;background:#07111F;border:1px solid rgba(255,255,255,.06);border-radius:12px;padding:4px;">
                    <button class="pos-qty-button" type="button" data-action="decrease" data-product-id="${item.id}" aria-label="Disminuir ${escapeHtml(item.name)}" style="width:30px;height:30px;border:none;border-radius:9px;background:#0B1726;color:white;font-size:18px;cursor:pointer;">-</button>
                    <div style="font-size:14px;font-weight:900;min-width:22px;text-align:center;color:white;">${item.quantity}</div>
                    <button class="pos-qty-button" type="button" data-action="increase" data-product-id="${item.id}" aria-label="Aumentar ${escapeHtml(item.name)}" style="width:30px;height:30px;border:none;border-radius:9px;background:#00D4FF;color:black;font-size:18px;font-weight:bold;cursor:pointer;">+</button>
                </div>

                <button class="pos-remove-button" type="button" data-action="remove" data-product-id="${item.id}" aria-label="Eliminar ${escapeHtml(item.name)}" style="width:36px;height:36px;border:1px solid rgba(255,91,110,.22);border-radius:11px;background:rgba(255,91,110,.08);color:#FF5B6E;cursor:pointer;font-size:16px;display:grid;place-items:center;">🗑</button>
            </div>
        `;

        return wrapper;
    };

    const renderCart = () => {
        const totals = getCartTotals();
        cartItems.innerHTML = "";

        if (cart.size === 0) {
            const emptyState = document.createElement("div");
            emptyState.id = "pos-cart-empty";
            emptyState.style.cssText = "color:#6D87A8;font-size:14px;text-align:center;margin-top:32px;";
            emptyState.textContent = "Selecciona productos para iniciar la orden.";
            cartItems.appendChild(emptyState);
        } else {
            cart.forEach((item) => cartItems.appendChild(createCartItem(item)));
        }

        cartCount.textContent = `${totals.itemCount} ${totals.itemCount === 1 ? "ITEM" : "ITEMS"}`;
        subtotalNode.textContent = formatMoney(totals.subtotal);
        taxNode.textContent = formatMoney(totals.tax);
        tipNode.textContent = formatMoney(totals.tip);
        totalNode.textContent = formatMoney(totals.total);
    };

    const applyProductFilters = () => {
        const query = (productSearchInput?.value || "").trim().toLowerCase();

        productCards.forEach((card) => {
            const matchesSearch = !query || (card.dataset.productSearch || "").toLowerCase().includes(query);
            const matchesCategory = !selectedCategoryId || card.dataset.categoryId === selectedCategoryId;
            card.style.display = matchesSearch && matchesCategory ? "" : "none";
        });

    };

    const setActiveCategory = (button) => {
        categoryFilters.forEach((filter) => {
            const isActive = filter === button;
            filter.style.background = isActive ? "#00D4FF" : "#0B1726";
            filter.style.color = isActive ? "black" : "#8FA7C0";
            filter.style.borderColor = isActive ? "transparent" : "rgba(255,255,255,.06)";
        });
    };

    const addProduct = (product) => {
        const existing = cart.get(product.id);

        if (existing) {
            existing.quantity += 1;
        } else {
            cart.set(product.id, {
                ...product,
                quantity: 1,
            });
        }

        renderCart();
        pulseOrderSummary();
    };

    const updateQuantity = (productId, delta) => {
        const item = cart.get(productId);

        if (!item) {
            return;
        }

        item.quantity += delta;

        if (item.quantity <= 0) {
            cart.delete(productId);
        }

        renderCart();
        pulseOrderSummary();
    };

    const createOrder = async () => {
        if (!selectedTable) {
            showTableRequiredModal();
            return;
        }

        if (activeOrder) {
            window.showToast(`La mesa ya tiene la orden #${activeOrder.order_id} en estado ${activeOrder.status_label}.`, "warning");
            return;
        }

        if (cart.size === 0) {
            window.showToast("Selecciona productos para iniciar la orden.", "warning");
            return;
        }

        sendOrderButton.disabled = true;

        try {
            const response = await fetch(posRoot.dataset.createOrderUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({
                    table_id: selectedTable.id,
                    items: Array.from(cart.values()).map((item) => ({
                        product_id: item.id,
                        quantity: item.quantity,
                    })),
                }),
            });
            const data = await readJsonResponse(response, "No se pudo crear la orden.");

            if (!response.ok || !data.success) {
                throw new Error(data.error || "No se pudo crear la orden.");
            }

            activeOrder = {
                order_id: data.order_id,
                status: "OPEN",
                status_label: "Abierta",
                subtotal: data.subtotal,
                tax: data.tax,
                total: data.total,
                created_at: new Date().toISOString(),
                table_id: selectedTable.id,
                table_name: selectedTable.name,
                table_capacity: selectedTable.capacity,
            };
            updateTableVisual(selectedTable.id, "OCCUPIED", "Abierta", activeOrder);
            cart.clear();
            renderCart();
            updateSelectedTableLabel();
            updateCheckoutState();
            if (data.auto_print_kitchen) {
                openPrintWindow(data.kitchen_print_url);
            }
            window.showToast(`Orden #${data.order_id} enviada a cocina.`, "success");
        } catch (error) {
            window.showToast(error.message, "error");
        } finally {
            sendOrderButton.disabled = false;
        }
    };

    const openPaymentModal = (method = selectedPaymentMethod) => {
        if (!selectedTable) {
            showTableRequiredModal();
            return;
        }

        if (!activeOrder) {
            window.showToast("La mesa seleccionada no tiene una orden activa.", "warning");
            return;
        }

        if (activeOrder.status !== "READY") {
            window.showToast("Solo puedes cobrar cuando la orden esté en estado Lista.", "warning");
            return;
        }

        setSelectedPaymentMethod(method);
        lastPaidOrderId = null;
        if (printActions) {
            printActions.hidden = true;
            printActions.style.display = "none";
        }
        if (paymentOrderLabel) {
            paymentOrderLabel.textContent = `Orden #${activeOrder.order_id} · ${selectedTable.name}`;
        }
        modalSubtotalNode.textContent = formatMoney(Number(activeOrder.subtotal || 0));
        modalTaxNode.textContent = formatMoney(Number(activeOrder.tax || 0));
        modalTotalNode.textContent = formatMoney(Number(activeOrder.total || 0));
        paymentModal.hidden = false;
        paymentModal.style.display = "flex";
    };

    const closePaymentModal = () => {
        if (!paymentModal) {
            return;
        }

        paymentModal.hidden = true;
        paymentModal.style.display = "none";
    };

    const payOrder = async () => {
        const response = await fetch(getTemplateUrl(posRoot.dataset.payOrderUrlTemplate, activeOrder.order_id), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
                payment_method: selectedPaymentMethod,
            }),
        });
        const data = await readJsonResponse(response, "No se pudo registrar el pago.");

        if (!response.ok || !data.success) {
            throw new Error(data.error || "No se pudo registrar el pago.");
        }

        return data;
    };

    const confirmPayment = async () => {
        confirmPaymentButton.disabled = true;
        checkoutButton.disabled = true;

        try {
            const payment = await payOrder();
            lastPaidOrderId = payment.order_id;
            activeOrder = null;
            updateTableVisual(payment.table_id, "FREE", "Libre");
            updateSelectedTableLabel();
            updateCheckoutState();
            if (printActions) {
                printActions.hidden = false;
                printActions.style.display = "grid";
            }
            if (payment.auto_print_cashier) {
                openPrintWindow(payment.receipt_print_url);
            }
            window.showToast(`Orden #${payment.order_id} pagada por ${formatMoney(Number(payment.total))}.`, "success");
        } catch (error) {
            window.showToast(error.message, "error");
            updateCheckoutState();
        } finally {
            confirmPaymentButton.disabled = false;
        }
    };

    addButtons.forEach((button) => {
        button.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();

            addProduct({
                id: button.dataset.productId,
                name: button.dataset.productName,
                description: button.dataset.productDescription,
                price: Number.parseFloat(button.dataset.productPrice || "0"),
            });
        });
    });

    productCards.forEach((card) => {
        const addFromCard = () => {
            addProduct({
                id: card.dataset.productId,
                name: card.dataset.productName,
                description: card.dataset.productDescription,
                price: Number.parseFloat(card.dataset.productPrice || "0"),
            });
        };

        card.addEventListener("click", addFromCard);
        card.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                addFromCard();
            }
        });
    });

    cartItems.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-action]");

        if (!button) {
            return;
        }

        const productId = button.dataset.productId;

        if (button.dataset.action === "increase") {
            updateQuantity(productId, 1);
        }

        if (button.dataset.action === "decrease") {
            updateQuantity(productId, -1);
        }

        if (button.dataset.action === "remove") {
            cart.delete(productId);
            renderCart();
            pulseOrderSummary();
        }
    });

    tableOptions.forEach((tableOption) => {
        tableOption.addEventListener("click", async () => {
            selectedTable = {
                id: tableOption.dataset.tableId || "",
                name: tableOption.dataset.tableName || tableOption.textContent.trim(),
                capacity: Number(tableOption.dataset.tableCapacity || "0"),
            };
            posRoot.dataset.tableId = selectedTable.id;

            tableOptions.forEach((option) => {
                option.style.boxShadow = "none";
            });
            tableOption.style.boxShadow = "0 0 0 2px rgba(0,212,255,.42)";
            syncActiveOrderFromDataset(tableOption);
            updateSelectedTableLabel();
            updateCheckoutState();

            try {
                await fetchActiveOrder(selectedTable.id);
            } catch (error) {
                window.showToast(error.message, "error");
            }
        });
    });

    categoryFilters.forEach((button) => {
        button.addEventListener("click", () => {
            selectedCategoryId = button.dataset.categoryId || "";
            setActiveCategory(button);
            applyProductFilters();
        });
    });

    if (productSearchInput) {
        productSearchInput.addEventListener("input", applyProductFilters);
    }

    if (sendOrderButton) {
        sendOrderButton.addEventListener("click", createOrder);
    }

    if (checkoutButton) {
        checkoutButton.addEventListener("click", () => openPaymentModal());
    }

    paymentMethodButtons.forEach((button) => {
        button.addEventListener("click", () => openPaymentModal(button.dataset.paymentMethod));
    });

    modalMethodButtons.forEach((button) => {
        button.addEventListener("click", () => setSelectedPaymentMethod(button.dataset.paymentMethod));
    });

    if (paymentClose) {
        paymentClose.addEventListener("click", closePaymentModal);
    }

    if (paymentModal) {
        paymentModal.addEventListener("click", (event) => {
            if (event.target === paymentModal) {
                closePaymentModal();
            }
        });
    }

    if (confirmPaymentButton) {
        confirmPaymentButton.addEventListener("click", confirmPayment);
    }

    if (tableRequiredClose) {
        tableRequiredClose.addEventListener("click", closeTableRequiredModal);
    }

    if (tableRequiredModal) {
        tableRequiredModal.addEventListener("click", (event) => {
            if (event.target === tableRequiredModal) {
                closeTableRequiredModal();
            }
        });
    }

    if (printTicketButton) {
        printTicketButton.addEventListener("click", () => {
            if (lastPaidOrderId) {
                window.open(getTemplateUrl(posRoot.dataset.ticketUrlTemplate, lastPaidOrderId), "_blank");
            }
        });
    }

    if (printKitchenButton) {
        printKitchenButton.addEventListener("click", () => {
            if (lastPaidOrderId) {
                window.open(getTemplateUrl(posRoot.dataset.kitchenTicketUrlTemplate, lastPaidOrderId), "_blank");
            }
        });
    }

    setSelectedPaymentMethod(selectedPaymentMethod);
    if (categoryFilters[0]) {
        setActiveCategory(categoryFilters[0]);
    }
    applyProductFilters();
    updateSelectedTableLabel();
    updateCheckoutState();
    renderCart();
});
