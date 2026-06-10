"""
Mock data for the conversational shopping demo.

Contains product catalog, user profiles with purchase history,
impressions, and loyalty points.
"""

PRODUCTS = [
    {
        "id": "P001",
        "name": "Silk Wrap Blouse",
        "category": "Tops",
        "price": 89.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Ivory", "Blush Pink", "Black"],
        "description": "Elegant silk wrap blouse with a flattering drape. Perfect for office-to-evening transitions.",
        "tags": ["silk", "elegant", "workwear", "blouse", "classic"],
        "image": "silk_wrap_blouse.png",
        "rating": 4.7,
        "reviews_count": 234,
    },
    {
        "id": "P002",
        "name": "High-Rise Straight Jeans",
        "category": "Bottoms",
        "price": 120.00,
        "sizes": ["24", "25", "26", "27", "28", "29", "30", "31", "32"],
        "colors": ["Indigo", "Light Wash", "Black"],
        "description": "Premium denim with a flattering high-rise straight cut. Sustainable organic cotton blend.",
        "tags": ["denim", "jeans", "sustainable", "casual", "everyday"],
        "image": "high_rise_straight_jeans.png",
        "rating": 4.8,
        "reviews_count": 567,
    },
    {
        "id": "P003",
        "name": "Cashmere Crew Sweater",
        "category": "Knitwear",
        "price": 195.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Camel", "Grey Melange", "Navy", "Cream"],
        "description": "Luxuriously soft 100% cashmere crew neck. A timeless wardrobe essential.",
        "tags": ["cashmere", "luxury", "knitwear", "classic", "winter"],
        "image": "cashmere_crew_sweater.png",
        "rating": 4.9,
        "reviews_count": 412,
    },
    {
        "id": "P004",
        "name": "Pleated Midi Skirt",
        "category": "Bottoms",
        "price": 75.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Emerald", "Burgundy", "Black", "Navy"],
        "description": "Flowing pleated midi skirt in luxe satin. Versatile enough for brunch or cocktails.",
        "tags": ["skirt", "midi", "elegant", "satin", "versatile"],
        "image": "pleated_midi_skirt.png",
        "rating": 4.5,
        "reviews_count": 189,
    },
    {
        "id": "P005",
        "name": "Oversized Blazer",
        "category": "Outerwear",
        "price": 165.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Charcoal", "Tan", "Black"],
        "description": "Modern oversized blazer with structured shoulders. The ultimate power piece.",
        "tags": ["blazer", "outerwear", "workwear", "power", "structured"],
        "image": "oversized_blazer.png",
        "rating": 4.6,
        "reviews_count": 321,
    },
    {
        "id": "P006",
        "name": "Linen Summer Dress",
        "category": "Dresses",
        "price": 110.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["White", "Sage", "Terracotta"],
        "description": "Breezy linen dress with a relaxed fit and adjustable waist tie. Summer essential.",
        "tags": ["linen", "dress", "summer", "casual", "vacation"],
        "image": "linen_summer_dress.png",
        "rating": 4.7,
        "reviews_count": 278,
    },
    {
        "id": "P007",
        "name": "Leather Crossbody Bag",
        "category": "Accessories",
        "price": 145.00,
        "sizes": ["One Size"],
        "colors": ["Black", "Cognac", "Olive"],
        "description": "Compact Italian leather crossbody with gold hardware. Fits phone, wallet, and essentials.",
        "tags": ["bag", "leather", "accessories", "crossbody", "italian"],
        "image": "leather_crossbody_bag.png",
        "rating": 4.8,
        "reviews_count": 456,
    },
    {
        "id": "P008",
        "name": "Wool-Blend Trench Coat",
        "category": "Outerwear",
        "price": 285.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Camel", "Black", "Grey"],
        "description": "Classic double-breasted trench in fine wool blend. Timeless silhouette with modern tailoring.",
        "tags": ["coat", "trench", "wool", "outerwear", "classic", "winter"],
        "image": "wool_blend_trench_coat.png",
        "rating": 4.9,
        "reviews_count": 198,
    },
    {
        "id": "P009",
        "name": "Ribbed Knit Tank Top",
        "category": "Tops",
        "price": 35.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["White", "Black", "Heather Grey", "Olive"],
        "description": "Everyday ribbed tank with a modern slim fit. Layer it or wear solo.",
        "tags": ["tank", "basics", "layering", "casual", "everyday"],
        "image": "ribbed_knit_tank.png",
        "rating": 4.4,
        "reviews_count": 892,
    },
    {
        "id": "P010",
        "name": "Wide-Leg Tailored Trousers",
        "category": "Bottoms",
        "price": 130.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Black", "Beige", "Charcoal"],
        "description": "Impeccably tailored wide-leg trousers with pressed creases. Office-ready sophistication.",
        "tags": ["trousers", "tailored", "workwear", "wide-leg", "formal"],
        "image": "wide_leg_trousers.png",
        "rating": 4.6,
        "reviews_count": 345,
    },
    {
        "id": "P011",
        "name": "Satin Camisole",
        "category": "Tops",
        "price": 55.00,
        "sizes": ["XS", "S", "M", "L", "XL"],
        "colors": ["Champagne", "Black", "Dusty Rose"],
        "description": "Delicate satin camisole with adjustable straps and lace trim. Dress up or down.",
        "tags": ["camisole", "satin", "elegant", "evening", "layering"],
        "image": "satin_camisole.png",
        "rating": 4.5,
        "reviews_count": 267,
    },
    {
        "id": "P012",
        "name": "Chunky Knit Cardigan",
        "category": "Knitwear",
        "price": 125.00,
        "sizes": ["XS/S", "M/L", "XL/XXL"],
        "colors": ["Oatmeal", "Rust", "Forest Green"],
        "description": "Cozy oversized cardigan in chunky cable knit. The ultimate layering piece for cooler days.",
        "tags": ["cardigan", "chunky", "cozy", "knitwear", "winter", "layering"],
        "image": "chunky_knit_cardigan.png",
        "rating": 4.7,
        "reviews_count": 534,
    },
]


# Mock user — pre-loaded with purchase history, browsing impressions, loyalty
MOCK_USER = {
    "id": "U001",
    "name": "Sarah Mitchell",
    "email": "sarah.mitchell@example.com",
    "loyalty_tier": "Gold",
    "loyalty_points": 2_340,
    "points_value_per_100": 5.00,  # 100 points = $5 discount
    "size_preferences": {
        "tops": "M",
        "bottoms": "28",
        "dresses": "M",
        "outerwear": "M",
        "knitwear": "M",
    },
    "style_preferences": ["classic", "elegant", "workwear", "sustainable"],
    "purchase_history": [
        {
            "product_id": "P001",
            "product_name": "Silk Wrap Blouse",
            "color": "Ivory",
            "size": "M",
            "date": "2025-11-15",
            "price": 89.00,
            "rating_given": 5,
        },
        {
            "product_id": "P002",
            "product_name": "High-Rise Straight Jeans",
            "color": "Indigo",
            "size": "28",
            "date": "2025-10-22",
            "price": 120.00,
            "rating_given": 5,
        },
        {
            "product_id": "P005",
            "product_name": "Oversized Blazer",
            "color": "Charcoal",
            "size": "M",
            "date": "2025-09-30",
            "price": 165.00,
            "rating_given": 4,
        },
        {
            "product_id": "P009",
            "product_name": "Ribbed Knit Tank Top",
            "color": "White",
            "size": "M",
            "date": "2025-12-05",
            "price": 35.00,
            "rating_given": 4,
        },
        {
            "product_id": "P010",
            "product_name": "Wide-Leg Tailored Trousers",
            "color": "Black",
            "size": "M",
            "date": "2026-01-10",
            "price": 130.00,
            "rating_given": 5,
        },
    ],
    "browsing_impressions": [
        {"product_id": "P003", "product_name": "Cashmere Crew Sweater", "views": 5, "last_viewed": "2026-03-05", "added_to_wishlist": True},
        {"product_id": "P008", "product_name": "Wool-Blend Trench Coat", "views": 3, "last_viewed": "2026-03-07", "added_to_wishlist": True},
        {"product_id": "P004", "product_name": "Pleated Midi Skirt", "views": 2, "last_viewed": "2026-02-28", "added_to_wishlist": False},
        {"product_id": "P007", "product_name": "Leather Crossbody Bag", "views": 4, "last_viewed": "2026-03-06", "added_to_wishlist": False},
        {"product_id": "P011", "product_name": "Satin Camisole", "views": 1, "last_viewed": "2026-03-01", "added_to_wishlist": False},
        {"product_id": "P012", "product_name": "Chunky Knit Cardigan", "views": 6, "last_viewed": "2026-03-08", "added_to_wishlist": False},
    ],
    "total_spend": 539.00,
    "member_since": "2024-06-15",
}


def get_product_by_id(product_id: str) -> dict | None:
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    return None


def search_products(query: str = "", category: str = "", max_price: float | None = None) -> list[dict]:
    """Search products by keyword, category, or price filter."""
    results = []
    query_lower = query.lower()
    for p in PRODUCTS:
        if category and p["category"].lower() != category.lower():
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        if query_lower:
            searchable = f"{p['name']} {p['description']} {' '.join(p['tags'])}".lower()
            if query_lower not in searchable:
                continue
        results.append(p)
    return results
