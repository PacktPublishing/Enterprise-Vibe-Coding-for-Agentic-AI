"""
Conversational Shopping — AI-powered Fashion E-commerce

A Flask web app featuring a full shopping experience with an AI personal
stylist chatbot that can recommend products and manage the cart.

Usage:
    python app.py
    Open http://127.0.0.1:5000 in your browser
"""

import asyncio
import copy
import io
import json
import logging
import os
import traceback
import uuid

from flask import Flask, Response, render_template, request, jsonify, send_file

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("shop")

from agents import (
    IMAGES_DIR,
    _loop,
    generate_product_image,
)
from agents.client import client
from agents.shopping_assistant import create_agent
from mock_data import PRODUCTS, MOCK_USER

# ---------------------------------------------------------------------------
# App-level state (in-memory for demo purposes)
# ---------------------------------------------------------------------------
cart = []
user = copy.deepcopy(MOCK_USER)

# ---------------------------------------------------------------------------
# Create agent wired to live cart / user state
# ---------------------------------------------------------------------------
log.info("Creating shopping agent...")
shopping_agent = create_agent(client, cart_ref=cart, user_ref=user, products_ref=PRODUCTS)
log.info("Shopping agent created: %s (type=%s)", shopping_agent.name, type(shopping_agent).__name__)

# One session per process keeps multi-turn memory for the demo's single user.
_agent_session = shopping_agent.create_session(session_id="demo-user")

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Product APIs
# ---------------------------------------------------------------------------

@app.route("/api/products")
def api_products():
    """Return the full product catalog."""
    category = request.args.get("category", "")
    products = PRODUCTS
    if category:
        products = [p for p in PRODUCTS if p["category"].lower() == category.lower()]
    return jsonify(products)


@app.route("/api/products/<product_id>")
def api_product_detail(product_id):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return jsonify(p)
    return jsonify({"error": "Not found"}), 404


# ---------------------------------------------------------------------------
# Cart APIs
# ---------------------------------------------------------------------------

@app.route("/api/cart")
def api_cart():
    total = sum(i["price"] * i["quantity"] for i in cart)
    return jsonify({"items": cart, "total": round(total, 2), "count": len(cart)})


@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    data = request.get_json()
    product_id = data.get("product_id")
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    item = {
        "product_id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "color": data.get("color", product["colors"][0]),
        "size": data.get("size", "M"),
        "quantity": int(data.get("quantity", 1)),
        "image": product["image"],
    }
    cart.append(item)
    return jsonify({"message": f"Added {product['name']}", "count": len(cart), "item": item})


@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    data = request.get_json()
    idx = int(data.get("index", -1))
    if 0 <= idx < len(cart):
        removed = cart.pop(idx)
        return jsonify({"message": f"Removed {removed['name']}", "count": len(cart)})
    return jsonify({"error": "Invalid index"}), 400


# ---------------------------------------------------------------------------
# User / Loyalty APIs
# ---------------------------------------------------------------------------

@app.route("/api/user")
def api_user():
    return jsonify({
        "name": user["name"],
        "loyalty_tier": user["loyalty_tier"],
        "loyalty_points": user["loyalty_points"],
        "points_value": f"${user['loyalty_points'] / 100 * user.get('points_value_per_100', 5):.2f}",
    })


# ---------------------------------------------------------------------------
# Chat API (streams agent response via SSE)
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    log.info("=" * 50)
    log.info("CHAT REQUEST: %s", user_message)
    log.info("=" * 50)

    def generate():
        try:
            # Run the agent in the shared async loop
            log.info("Dispatching to agent (session=%s)...", _agent_session)
            future = asyncio.run_coroutine_threadsafe(
                _run_agent(user_message),
                _loop,
            )
            result = future.result(timeout=120)
            log.info("Agent response received (%d chars)", len(result["text"]))
            log.info("Agent reply: %s", result["text"][:300])

            yield "data: " + json.dumps({"type": "message", "text": result["text"]}) + "\n\n"

            # If cart was modified by the agent, push updated cart
            total = sum(i["price"] * i["quantity"] for i in cart)
            yield "data: " + json.dumps({
                "type": "cart_update",
                "cart": {"items": cart, "total": round(total, 2), "count": len(cart)},
            }) + "\n\n"

            yield "data: " + json.dumps({"type": "done"}) + "\n\n"
        except Exception as e:
            log.error("CHAT ERROR: %s", e)
            log.error(traceback.format_exc())
            yield "data: " + json.dumps({"type": "error", "text": str(e)}) + "\n\n"

    return Response(generate(), content_type="text/event-stream")


async def _run_agent(user_message: str) -> dict:
    """Run the shopping agent and return its response."""
    log.info("[Agent] Running agent.run() with message: %s", user_message[:100])

    result = await shopping_agent.run(user_message, session=_agent_session)

    log.info("[Agent] Result type: %s", type(result).__name__)
    log.info("[Agent] Result text: %s", str(result.text)[:300] if result.text else "(empty)")

    response_text = str(result.text) if result.text else "I'm sorry, I couldn't process that request."
    return {"text": response_text}


# ---------------------------------------------------------------------------
# Product image generation / serving
# ---------------------------------------------------------------------------

@app.route("/api/generate-image/<product_id>")
def api_generate_image(product_id):
    """Generate an AI product image on-the-fly (cached to disk)."""
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    img_path = os.path.join(IMAGES_DIR, product["image"])
    if not os.path.exists(img_path):
        prompt = (
            f"Professional fashion e-commerce product photo of a {product['name']}. "
            f"{product['description']} "
            f"Clean white background, studio lighting, high-end fashion photography style. "
            f"Color: {product['colors'][0]}. No text or watermarks."
        )
        try:
            img_bytes = generate_product_image(prompt, size="1024x1024")
            with open(img_path, "wb") as f:
                f.write(img_bytes)
        except Exception:
            # Return a placeholder on failure
            return send_placeholder(product["name"])

    return send_file(img_path, mimetype="image/png")


@app.route("/generated_images/<filename>")
def serve_generated_image(filename):
    path = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(path):
        return send_file(path, mimetype="image/png")
    return "", 404


def send_placeholder(name: str):
    """Generate an SVG placeholder with the product name."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="500" viewBox="0 0 400 500">
    <rect width="400" height="500" fill="#f0f0f0"/>
    <text x="200" y="240" font-family="Arial" font-size="16" fill="#999" text-anchor="middle">{name}</text>
    <text x="200" y="270" font-family="Arial" font-size="12" fill="#bbb" text-anchor="middle">Image generating...</text>
    </svg>"""
    return Response(svg, mimetype="image/svg+xml")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print("=" * 60)
    print("  LUXE Fashion — Conversational Shopping Experience")
    print(f"  http://127.0.0.1:{port}")
    print("=" * 60)
    app.run(debug=True, port=port, use_reloader=False)
