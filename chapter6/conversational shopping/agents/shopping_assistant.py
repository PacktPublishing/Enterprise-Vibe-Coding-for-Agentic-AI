"""
Shopping Assistant Agent — conversational AI for the fashion store.

Has function tools to browse products, manage the cart, look up user
profile / loyalty, and add items to the cart on behalf of the user.
"""

import json
from typing import Annotated

from pydantic import Field
from agent_framework import Agent, tool

# ---------------------------------------------------------------------------
# Tool functions (called by the agent via function-calling)
# ---------------------------------------------------------------------------

_cart = []          # will be replaced at init with the app-level reference
_user = {}          # will be replaced at init with mock user dict
_products = []      # will be replaced at init with product catalog


@tool(name="get_user_profile", description="Get the current user's profile: loyalty tier, points, size preferences, style preferences, and spend history.")
def _get_user_profile() -> str:
    """Return the current user's profile including loyalty, purchase history and preferences."""
    profile = {
        "name": _user.get("name"),
        "loyalty_tier": _user.get("loyalty_tier"),
        "loyalty_points": _user.get("loyalty_points"),
        "points_value": f"${_user['loyalty_points'] / 100 * _user.get('points_value_per_100', 5):.2f}",
        "size_preferences": _user.get("size_preferences"),
        "style_preferences": _user.get("style_preferences"),
        "member_since": _user.get("member_since"),
        "total_spend": _user.get("total_spend"),
    }
    return json.dumps(profile)


@tool(name="get_purchase_history", description="Get the user's past purchase history with dates, items, prices, and ratings.")
def _get_purchase_history() -> str:
    """Return the user's past purchases."""
    return json.dumps(_user.get("purchase_history", []))


@tool(name="get_browsing_impressions", description="Get products the user has recently browsed or added to their wishlist.")
def _get_browsing_impressions() -> str:
    """Return products the user has recently viewed or wishlisted."""
    return json.dumps(_user.get("browsing_impressions", []))


@tool(name="search_products", description="Search the product catalog. Parameters: query (keyword), category (Tops/Bottoms/Dresses/Outerwear/Knitwear/Accessories), max_price (number).")
def _search_products(
    query: Annotated[str, Field(description="Keyword to search for", default="")] = "",
    category: Annotated[str, Field(description="Product category filter", default="")] = "",
    max_price: Annotated[str, Field(description="Maximum price filter", default="")] = "",
) -> str:
    """Search the product catalog by keyword, category, or max price."""
    query_lower = query.lower()
    max_p = float(max_price) if max_price else None
    results = []
    for p in _products:
        if category and p["category"].lower() != category.lower():
            continue
        if max_p is not None and p["price"] > max_p:
            continue
        if query_lower:
            searchable = f"{p['name']} {p['description']} {' '.join(p['tags'])}".lower()
            if query_lower not in searchable:
                continue
        results.append({
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "colors": p["colors"],
            "sizes": p["sizes"],
            "rating": p["rating"],
            "description": p["description"],
        })
    return json.dumps(results)


@tool(name="get_product_details", description="Get full details for a product by its ID (e.g. P001).")
def _get_product_details(
    product_id: Annotated[str, Field(description="The product ID, e.g. P001")],
) -> str:
    """Get full details for a specific product by ID."""
    for p in _products:
        if p["id"] == product_id:
            return json.dumps(p)
    return json.dumps({"error": f"Product {product_id} not found"})


@tool(name="add_to_cart", description="Add a product to the shopping cart. Use this when the user asks to add something or when you recommend something and they agree.")
def _add_to_cart(
    product_id: Annotated[str, Field(description="The product ID to add, e.g. P001")],
    color: Annotated[str, Field(description="Color choice", default="")] = "",
    size: Annotated[str, Field(description="Size choice", default="")] = "",
    quantity: Annotated[str, Field(description="Quantity to add", default="1")] = "1",
) -> str:
    """Add a product to the user's cart. Returns the updated cart."""
    product = None
    for p in _products:
        if p["id"] == product_id:
            product = p
            break
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    qty = int(quantity) if quantity else 1
    item = {
        "product_id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "color": color or product["colors"][0],
        "size": size or "M",
        "quantity": qty,
        "image": product["image"],
    }
    _cart.append(item)
    return json.dumps({"message": f"Added {qty}x {product['name']} ({item['color']}, {item['size']}) to cart", "cart_count": len(_cart), "item": item})


@tool(name="get_cart", description="Get the current shopping cart contents and total price.")
def _get_cart() -> str:
    """Return the current shopping cart contents and total."""
    total = sum(i["price"] * i["quantity"] for i in _cart)
    return json.dumps({"items": _cart, "total": total, "item_count": len(_cart)})


@tool(name="remove_from_cart", description="Remove an item from the cart by its 0-based index.")
def _remove_from_cart(
    index: Annotated[str, Field(description="0-based index of the cart item to remove")],
) -> str:
    """Remove an item from the cart by its index (0-based)."""
    idx = int(index)
    if 0 <= idx < len(_cart):
        removed = _cart.pop(idx)
        return json.dumps({"message": f"Removed {removed['name']} from cart", "cart_count": len(_cart)})
    return json.dumps({"error": "Invalid cart index"})


@tool(name="calculate_loyalty_discount", description="Calculate how much discount the user's loyalty points are worth.")
def _calculate_loyalty_discount() -> str:
    """Calculate how much discount the user can get from loyalty points."""
    points = _user.get("loyalty_points", 0)
    rate = _user.get("points_value_per_100", 5.0)
    discount = points / 100 * rate
    return json.dumps({
        "available_points": points,
        "discount_value": f"${discount:.2f}",
        "loyalty_tier": _user.get("loyalty_tier"),
    })


# ---------------------------------------------------------------------------
# Tool list for the agent
# ---------------------------------------------------------------------------

TOOLS = [
    _get_user_profile,
    _get_purchase_history,
    _get_browsing_impressions,
    _search_products,
    _get_product_details,
    _add_to_cart,
    _get_cart,
    _remove_from_cart,
    _calculate_loyalty_discount,
]

# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

INSTRUCTIONS = """You are **StyleBot**, the personal shopping assistant for LUXE Fashion, an upscale online fashion retailer.

You have access to tools that let you:
- Look up the customer's profile, purchase history, browsing behavior, and loyalty points
- Search the product catalog
- Add and remove items from their shopping cart
- Calculate loyalty discounts

## Your personality
- Warm, knowledgeable, and fashion-savvy — like a personal stylist
- Proactive: you suggest items and outfits based on what you know about the customer
- Concise but enthusiastic — keep replies short and scannable
- Use emoji sparingly for warmth (1-2 per message max)

## Key behaviors
1. **Greet proactively**: On the first message, immediately fetch the user profile and browsing history. Reference something specific (e.g., an item they've been eyeing, their loyalty points balance, or a past favorite) to show you know them.
2. **Recommend smartly**: Base suggestions on their purchase history (what styles they like, their sizes), browsing impressions (what they've viewed recently), and style preferences. Always mention available sizes and colors.
3. **Add to cart seamlessly**: When a user says "yes", "add it", "sounds good", "I'll take it", or similar affirmative, immediately add the item to their cart using the tool — don't ask them to click a button.
4. **Loyalty program**: Proactively mention their loyalty points and potential savings. If they're close to a tier upgrade, mention it.
5. **Outfit building**: When they buy one piece, suggest complementary items to complete an outfit.
6. **Be honest**: If something might not suit their style based on history, say so gently and suggest alternatives.

## Formatting
- Use **bold** for product names and prices
- Use line breaks for readability
- When showing multiple products, use a brief list format
- Do NOT output raw JSON — always use natural, conversational language

When adding to cart, confirm what you added (name, color, size, price) and mention the updated cart total."""


def create_agent(client, cart_ref, user_ref, products_ref):
    """Create the shopping assistant agent and wire up tool state."""
    global _cart, _user, _products
    _cart = cart_ref
    _user = user_ref
    _products = products_ref

    return Agent(
        client,
        INSTRUCTIONS,
        name="StyleBot",
        tools=TOOLS,
    )
