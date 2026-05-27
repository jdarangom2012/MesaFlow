document.addEventListener("DOMContentLoaded", () => {
    const IVA_RATE = 0.19;
    const cart = new Map();

    const addButtons = document.querySelectorAll(".pos-add-product");
    const cartItems = document.getElementById("pos-cart-items");
    const cartCount = document.getElementById("pos-cart-count");
    const subtotalNode = document.getElementById("pos-subtotal");
    const taxNode = document.getElementById("pos-tax");
    const tipNode = document.getElementById("pos-tip");
    const totalNode = document.getElementById("pos-total");
    const checkoutButton = document.getElementById("pos-checkout-button");
    const posRoot = document.querySelector("[data-create-order-url]");
    const tableOptions = document.querySelectorAll(".pos-table-option");

    if (!cartItems || !cartCount || !subtotalNode || !taxNode || !tipNode || !totalNode) {
        return;
    }

    const moneyFormatter = new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0,
    });

    const formatMoney = (value) => moneyFormatter.format(value);

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

    const createCartItem = (item) => {
        const wrapper = document.createElement("div");
        wrapper.style.cssText = "background:#111C2D;border-radius:18px;padding:16px;margin-bottom:14px;";

        wrapper.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                <div>
                    <div style="font-size:17px;font-weight:700;color:white;">
                        ${escapeHtml(item.name)}
                    </div>
                    <div style="color:#6D87A8;font-size:13px;margin-top:5px;">
                        ${escapeHtml(item.description || "Producto seleccionado")}
                    </div>
                </div>
                <div style="color:#00D4FF;font-weight:800;font-size:18px;white-space:nowrap;">
                    ${formatMoney(item.price * item.quantity)}
                </div>
            </div>

            <div style="margin-top:14px;display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <button type="button" data-action="decrease" data-product-id="${item.id}" style="width:34px;height:34px;border:none;border-radius:10px;background:#07111F;color:white;font-size:20px;cursor:pointer;">
                        -
                    </button>

                    <div style="font-size:16px;font-weight:700;min-width:20px;text-align:center;">
                        ${item.quantity}
                    </div>

                    <button type="button" data-action="increase" data-product-id="${item.id}" style="width:34px;height:34px;border:none;border-radius:10px;background:#00D4FF;color:black;font-size:20px;font-weight:bold;cursor:pointer;">
                        +
                    </button>
                </div>

                <button type="button" data-action="remove" data-product-id="${item.id}" style="border:none;background:none;color:#FF5B6E;cursor:pointer;font-size:13px;">
                    Eliminar
                </button>
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
    };

    const createOrder = async () => {
        if (!checkoutButton || !posRoot || cart.size === 0) {
            return;
        }

        const tableId = posRoot.dataset.tableId;

        if (!tableId) {
            window.alert("Selecciona una mesa antes de cobrar.");
            return;
        }

        checkoutButton.disabled = true;

        try {
            const response = await fetch(posRoot.dataset.createOrderUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({
                    table_id: tableId,
                    items: Array.from(cart.values()).map((item) => ({
                        product_id: item.id,
                        quantity: item.quantity,
                    })),
                }),
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || "No se pudo crear la orden.");
            }

            cart.clear();
            renderCart();
            window.alert(`Orden #${data.order_id} creada por ${formatMoney(Number(data.total))}.`);
        } catch (error) {
            window.alert(error.message);
        } finally {
            checkoutButton.disabled = false;
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
        }
    });

    tableOptions.forEach((tableOption) => {
        tableOption.addEventListener("click", () => {
            if (posRoot) {
                posRoot.dataset.tableId = tableOption.dataset.tableId || "";
            }
        });
    });

    if (checkoutButton) {
        checkoutButton.addEventListener("click", createOrder);
    }

    renderCart();
});
