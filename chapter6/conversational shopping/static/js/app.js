/* ===================================================================
   LUXE Fashion — Conversational Shopping Frontend
   =================================================================== */

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let products = [];
let cartData = { items: [], total: 0, count: 0 };
let chatOpen = false;
let currentCategory = "";
let selectedProduct = null;
let selectedColor = "";
let selectedSize = "";

// Color name -> CSS value mapping for swatches
const COLOR_MAP = {
    "ivory": "#FFFFF0", "blush pink": "#FFB6C1", "black": "#1a1a1a",
    "indigo": "#3F51B5", "light wash": "#B0C4DE", "camel": "#C19A6B",
    "grey melange": "#A9A9A9", "navy": "#1B2A4A", "cream": "#FFFDD0",
    "emerald": "#50C878", "burgundy": "#800020", "charcoal": "#36454F",
    "tan": "#D2B48C", "white": "#FFFFFF", "sage": "#BCB88A",
    "terracotta": "#E2725B", "cognac": "#9A463D", "olive": "#808000",
    "grey": "#808080", "heather grey": "#B6B6B4",
    "champagne": "#F7E7CE", "dusty rose": "#DCAE96",
    "oatmeal": "#D3C4A5", "rust": "#B7410E", "forest green": "#228B22",
    "beige": "#F5F5DC",
};

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    loadProducts();
    loadCart();
    loadUser();
    setupCategoryNav();
    createToastContainer();
});

// ---------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------
async function loadProducts(category = "") {
    const url = category ? `/api/products?category=${encodeURIComponent(category)}` : "/api/products";
    const res = await fetch(url);
    products = await res.json();
    renderProducts();
}

function renderProducts() {
    const grid = document.getElementById("productsGrid");
    const countEl = document.getElementById("productCount");
    const titleEl = document.getElementById("sectionTitle");
    titleEl.textContent = currentCategory || "All Products";
    countEl.textContent = `${products.length} items`;

    grid.innerHTML = products.map(p => `
        <div class="product-card" onclick="openProductModal('${p.id}')">
            <div class="product-image">
                <img src="/api/generate-image/${p.id}" alt="${p.name}"
                     onerror="this.parentElement.innerHTML='<div class=\\'product-image-placeholder\\'>${p.name}</div>'"
                     loading="lazy">
                <button class="quick-add" onclick="event.stopPropagation(); quickAdd('${p.id}')">+ Quick Add</button>
            </div>
            <div class="product-info">
                <h3>${p.name}</h3>
                <div class="product-price">$${p.price.toFixed(2)}</div>
                <div class="product-rating">★ ${p.rating} · ${p.reviews_count} reviews</div>
                <div class="product-colors">
                    ${p.colors.map(c => `<span class="color-dot" style="background:${getColor(c)}" title="${c}"></span>`).join("")}
                </div>
            </div>
        </div>
    `).join("");
}

function getColor(name) {
    return COLOR_MAP[name.toLowerCase()] || "#ccc";
}

function setupCategoryNav() {
    document.querySelectorAll(".nav-link[data-category]").forEach(link => {
        link.addEventListener("click", e => {
            e.preventDefault();
            document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
            link.classList.add("active");
            currentCategory = link.dataset.category;
            loadProducts(currentCategory);
        });
    });
}

// ---------------------------------------------------------------------------
// Product Modal
// ---------------------------------------------------------------------------
function openProductModal(productId) {
    const p = products.find(x => x.id === productId);
    if (!p) return;
    selectedProduct = p;
    selectedColor = p.colors[0];
    selectedSize = p.sizes.includes("M") ? "M" : p.sizes[0];

    document.getElementById("modalImage").src = `/api/generate-image/${p.id}`;
    document.getElementById("modalCategory").textContent = p.category;
    document.getElementById("modalName").textContent = p.name;
    document.getElementById("modalPrice").textContent = `$${p.price.toFixed(2)}`;
    document.getElementById("modalRating").textContent = `★ ${p.rating} · ${p.reviews_count} reviews`;
    document.getElementById("modalDescription").textContent = p.description;

    // Colors
    document.getElementById("modalColors").innerHTML = p.colors.map(c =>
        `<div class="color-option ${c === selectedColor ? 'selected' : ''}"
              style="background:${getColor(c)}" title="${c}"
              onclick="selectColor('${c}', this)"></div>`
    ).join("");

    // Sizes
    document.getElementById("modalSizes").innerHTML = p.sizes.map(s =>
        `<div class="size-option ${s === selectedSize ? 'selected' : ''}"
              onclick="selectSize('${s}', this)">${s}</div>`
    ).join("");

    // Add to cart btn
    document.getElementById("modalAddToCart").onclick = () => addToCartFromModal();

    document.getElementById("productModal").classList.add("open");
}

function closeProductModal() {
    document.getElementById("productModal").classList.remove("open");
    selectedProduct = null;
}

function selectColor(color, el) {
    selectedColor = color;
    el.parentElement.querySelectorAll(".color-option").forEach(e => e.classList.remove("selected"));
    el.classList.add("selected");
}

function selectSize(size, el) {
    selectedSize = size;
    el.parentElement.querySelectorAll(".size-option").forEach(e => e.classList.remove("selected"));
    el.classList.add("selected");
}

async function addToCartFromModal() {
    if (!selectedProduct) return;
    await addToCart(selectedProduct.id, selectedColor, selectedSize);
    closeProductModal();
}

async function quickAdd(productId) {
    const p = products.find(x => x.id === productId);
    if (!p) return;
    await addToCart(p.id, p.colors[0], p.sizes.includes("M") ? "M" : p.sizes[0]);
}

// ---------------------------------------------------------------------------
// Cart
// ---------------------------------------------------------------------------
async function loadCart() {
    const res = await fetch("/api/cart");
    cartData = await res.json();
    updateCartUI();
}

async function addToCart(productId, color, size, quantity = 1) {
    const res = await fetch("/api/cart/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: productId, color, size, quantity }),
    });
    const data = await res.json();
    await loadCart();
    showToast(`✓ ${data.message}`);
}

async function removeFromCart(index) {
    await fetch("/api/cart/remove", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index }),
    });
    await loadCart();
}

function updateCartUI() {
    const countEl = document.getElementById("cartCount");
    const itemsEl = document.getElementById("cartItems");
    const footerEl = document.getElementById("cartFooter");
    const totalEl = document.getElementById("cartTotal");
    const loyaltyNote = document.getElementById("cartLoyaltyNote");

    countEl.textContent = cartData.count;

    if (cartData.items.length === 0) {
        itemsEl.innerHTML = '<div class="cart-empty">Your bag is empty</div>';
        footerEl.style.display = "none";
        return;
    }

    footerEl.style.display = "block";
    totalEl.textContent = `$${cartData.total.toFixed(2)}`;
    loyaltyNote.textContent = `★ You'll earn ${Math.floor(cartData.total)} loyalty points with this purchase`;

    itemsEl.innerHTML = cartData.items.map((item, i) => `
        <div class="cart-item">
            <div class="cart-item-image">
                <img src="/api/generate-image/${item.product_id}" alt="${item.name}"
                     onerror="this.style.display='none'">
            </div>
            <div class="cart-item-info">
                <h4>${item.name}</h4>
                <div class="cart-item-meta">${item.color} · ${item.size} · Qty ${item.quantity}</div>
                <div class="cart-item-price">$${(item.price * item.quantity).toFixed(2)}</div>
                <button class="cart-item-remove" onclick="removeFromCart(${i})">Remove</button>
            </div>
        </div>
    `).join("");
}

function toggleCart() {
    const sidebar = document.getElementById("cartSidebar");
    const overlay = document.getElementById("cartOverlay");
    sidebar.classList.toggle("open");
    overlay.classList.toggle("open");
}

// ---------------------------------------------------------------------------
// User / Loyalty
// ---------------------------------------------------------------------------
async function loadUser() {
    const res = await fetch("/api/user");
    const user = await res.json();
    document.getElementById("userGreeting").textContent = `Hi, ${user.name.split(" ")[0]}`;
    document.getElementById("loyaltyTier").textContent = user.loyalty_tier;
    document.getElementById("loyaltyPoints").textContent = `${user.loyalty_points.toLocaleString()} pts`;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------
function toggleChat() {
    chatOpen = !chatOpen;
    const panel = document.getElementById("chatPanel");
    const openIcon = document.querySelector(".chat-icon-open");
    const closeIcon = document.querySelector(".chat-icon-close");
    const notification = document.getElementById("chatNotification");

    if (chatOpen) {
        panel.classList.add("open");
        openIcon.style.display = "none";
        closeIcon.style.display = "block";
        notification.style.display = "none";
        document.getElementById("chatInput").focus();
    } else {
        panel.classList.remove("open");
        openIcon.style.display = "block";
        closeIcon.style.display = "none";
    }
}

function sendSuggestion(text) {
    document.getElementById("chatInput").value = text;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";

    // Remove welcome & suggestions on first message
    const welcome = document.querySelector(".chat-welcome");
    if (welcome) welcome.remove();

    appendChatBubble(text, "user");
    const typingEl = showTyping();

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let botMessage = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split("\n");
            buffer = lines.pop(); // keep incomplete line

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const payload = JSON.parse(line.slice(6));

                if (payload.type === "message") {
                    botMessage = payload.text;
                }
                if (payload.type === "error") {
                    botMessage = "⚠️ " + (payload.text || "Something went wrong. Please try again.");
                }
                if (payload.type === "cart_update") {
                    cartData = payload.cart;
                    updateCartUI();
                }
            }
        }

        typingEl.remove();
        if (botMessage) {
            appendChatBubble(botMessage, "bot");
        }
    } catch (err) {
        typingEl.remove();
        appendChatBubble("Sorry, I had trouble connecting. Please try again!", "bot");
    }
}

function appendChatBubble(text, sender) {
    const container = document.getElementById("chatMessages");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;
    // Support basic markdown bold
    bubble.innerHTML = text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

function showTyping() {
    const container = document.getElementById("chatMessages");
    const typing = document.createElement("div");
    typing.className = "chat-typing";
    typing.innerHTML = "<span></span><span></span><span></span>";
    container.appendChild(typing);
    container.scrollTop = container.scrollHeight;
    return typing;
}

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------
function createToastContainer() {
    if (!document.querySelector(".toast-container")) {
        const div = document.createElement("div");
        div.className = "toast-container";
        document.body.appendChild(div);
    }
}

function showToast(message) {
    const container = document.querySelector(".toast-container");
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<span class="toast-icon">🛍</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = "0"; toast.style.transition = "opacity 0.3s"; }, 2500);
    setTimeout(() => toast.remove(), 2800);
}
