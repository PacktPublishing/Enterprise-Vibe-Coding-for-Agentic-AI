"""
Hotel Agent — searches hotels and handles bookings (mock data).
"""

import json
import uuid
from typing import Annotated

from agent_framework import Agent, tool

INSTRUCTIONS = (
    "You are a Hotel Booking Specialist.\n\n"
    "1. Use search_hotels to find available hotels.\n"
    "2. Present options with name, stars, rating, price, and amenities.\n"
    "3. Help the customer choose and use book_hotel to confirm.\n"
    "4. After completing your task, hand off back to triage_agent.\n\n"
    "Do NOT hand off to any other specialist. Only hand off back to triage_agent.\n"
    "If dates or city are missing, ask."
)


@tool
def search_hotels(
    city: Annotated[str, "City name"],
    checkin: Annotated[str, "Check-in date (YYYY-MM-DD)"],
    checkout: Annotated[str, "Check-out date (YYYY-MM-DD)"],
) -> str:
    """Search available hotels in a city for the specified dates."""
    hotels = [
        {"id": "HT-1001", "name": "Le Grand Palace", "stars": 5, "rating": "9.2/10", "price": "$320/night",
         "amenities": ["Spa", "Pool", "Fine dining", "Concierge"]},
        {"id": "HT-2002", "name": "City Boutique Hotel", "stars": 4, "rating": "8.7/10", "price": "$185/night",
         "amenities": ["Rooftop bar", "Gym", "Free breakfast"]},
        {"id": "HT-3003", "name": "Comfort Inn Express", "stars": 3, "rating": "7.9/10", "price": "$95/night",
         "amenities": ["Free WiFi", "Parking", "Continental breakfast"]},
    ]
    return json.dumps({"city": city, "checkin": checkin, "checkout": checkout, "hotels": hotels}, indent=2)


@tool
def book_hotel(
    hotel_id: Annotated[str, "Hotel ID to book (e.g. HT-1001)"],
    guest_name: Annotated[str, "Guest full name"],
    nights: Annotated[int, "Number of nights"],
) -> str:
    """Book a hotel room. Returns confirmation."""
    code = "HB-" + uuid.uuid4().hex[:8].upper()
    return (
        f"Hotel {hotel_id} booked for {guest_name} ({nights} night(s)).\n"
        f"Confirmation Code: {code}\n"
        f"Booking details sent to email."
    )


def create_agent(client):
    """Create the hotel booking specialist agent."""
    return Agent(
        client,
        INSTRUCTIONS,
        name="hotel_agent",
        description="Hotel search and booking specialist.",
        tools=[search_hotels, book_hotel],
        require_per_service_call_history_persistence=True,
    )
