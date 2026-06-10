"""
Flight Agent — searches real flight schedules via AviationStack and handles bookings.
"""

import json
import uuid
from datetime import date as date_mod
from typing import Annotated

import httpx

from agent_framework import Agent, tool
from .client import AVIATIONSTACK_API_KEY

# Common city-to-IATA mappings for user convenience
CITY_TO_IATA = {
    "new york": "JFK", "nyc": "JFK", "jfk": "JFK", "newark": "EWR",
    "los angeles": "LAX", "la": "LAX", "san francisco": "SFO", "sf": "SFO",
    "chicago": "ORD", "miami": "MIA", "boston": "BOS", "seattle": "SEA",
    "dallas": "DFW", "atlanta": "ATL", "denver": "DEN", "washington": "IAD",
    "london": "LHR", "heathrow": "LHR", "gatwick": "LGW",
    "paris": "CDG", "rome": "FCO", "madrid": "MAD", "amsterdam": "AMS",
    "frankfurt": "FRA", "munich": "MUC", "berlin": "BER",
    "tokyo": "NRT", "narita": "NRT", "haneda": "HND",
    "osaka": "KIX", "seoul": "ICN", "beijing": "PEK", "shanghai": "PVG",
    "hong kong": "HKG", "singapore": "SIN", "bangkok": "BKK",
    "dubai": "DXB", "istanbul": "IST", "sydney": "SYD",
    "toronto": "YYZ", "mexico city": "MEX", "sao paulo": "GRU",
}


def _resolve_iata(value: str) -> str:
    """Convert a city name or IATA code to an IATA code."""
    v = value.strip().lower()
    if v in CITY_TO_IATA:
        return CITY_TO_IATA[v]
    # If it's already 3 letters, assume it's an IATA code
    if len(v) == 3 and v.isalpha():
        return v.upper()
    return value.upper()


INSTRUCTIONS = (
    "You are a Flight Booking Specialist.\n\n"
    "Today's date is: {today}\n\n"
    "1. Use search_flights to find available flights. This calls a real flight "
    "   schedule API that shows TODAY's active flights for a route.\n"
    "2. IMPORTANT: The API only returns today's schedule (not future dates). "
    "   If the user asks for a future date, search anyway and present the results "
    "   as 'typical flights on this route' that they could book for their date.\n"
    "3. The tool accepts city names (e.g. 'NYC', 'Tokyo') or IATA codes (e.g. 'JFK', 'NRT').\n"
    "4. Present results clearly with airline, flight number, times, and status.\n"
    "5. If a specific route has no results, suggest checking nearby airports.\n"
    "6. Help the customer choose and use book_flight to confirm.\n"
    "7. After completing your task AND presenting results to the user, "
    "   hand off back to triage_agent.\n\n"
    "IMPORTANT:\n"
    "- Do NOT hand off until you have given the user a complete, useful answer.\n"
    "- Only hand off back to triage_agent (no other specialist).\n"
    "- If cities are missing, ask the customer."
)


@tool
def search_flights(
    origin: Annotated[str, "Departure city name or IATA code (e.g. 'NYC', 'JFK', 'London', 'LHR')"],
    destination: Annotated[str, "Arrival city name or IATA code (e.g. 'Tokyo', 'NRT', 'Paris', 'CDG')"],
    date: Annotated[str, "Travel date (YYYY-MM-DD) - note: best results for today's date"] = "",
) -> str:
    """Search available flights between two airports using live AviationStack data."""
    dep_iata = _resolve_iata(origin)
    arr_iata = _resolve_iata(destination)

    if not AVIATIONSTACK_API_KEY:
        return json.dumps({
            "note": "AVIATIONSTACK_API_KEY not configured - showing demo data.",
            "from": dep_iata, "to": arr_iata,
            "flights": [
                {"flight": "DEMO-101", "airline": "DemoAir", "dep_time": "08:30", "arr_time": "12:45", "status": "scheduled"},
                {"flight": "DEMO-202", "airline": "DemoJet", "dep_time": "14:00", "arr_time": "18:15", "status": "scheduled"},
            ],
        }, indent=2)

    try:
        # Free tier does NOT support flight_date - always returns today's schedule
        params = {
            "access_key": AVIATIONSTACK_API_KEY,
            "dep_iata": dep_iata,
            "arr_iata": arr_iata,
            "limit": 10,
        }

        resp = httpx.get("http://api.aviationstack.com/v1/flights", params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            err_msg = data["error"].get("message", "API error") if isinstance(data["error"], dict) else str(data["error"])
            return json.dumps({"error": err_msg, "from": dep_iata, "to": arr_iata})

        flights = _extract_flights(data)

        # If no results with combined filter, try departure-only and note it
        if not flights:
            params_fallback = {
                "access_key": AVIATIONSTACK_API_KEY,
                "dep_iata": dep_iata,
                "limit": 20,
            }
            resp2 = httpx.get("http://api.aviationstack.com/v1/flights", params=params_fallback, timeout=15.0)
            resp2.raise_for_status()
            data2 = resp2.json()
            flights = _extract_flights(data2)

            if flights:
                return json.dumps({
                    "from": dep_iata, "to": arr_iata, "date": date or "today",
                    "note": f"No direct {dep_iata}->{arr_iata} flights found for the requested date. "
                            f"The free API tier only supports today's schedule. "
                            f"Here are today's flights departing from {dep_iata} as reference:",
                    "flights": flights[:10],
                }, indent=2)
            else:
                return json.dumps({
                    "from": dep_iata, "to": arr_iata, "date": date or "today",
                    "flights": [],
                    "message": f"No flights found departing from {dep_iata} in current data.",
                })

        return json.dumps({
            "from": dep_iata, "to": arr_iata, "date": date or "today",
            "flights": flights,
        }, indent=2)

    except httpx.TimeoutException:
        return json.dumps({"error": "Flight API request timed out. Please try again.", "from": dep_iata, "to": arr_iata})
    except Exception as exc:
        return json.dumps({"error": f"Could not fetch flights: {exc}", "from": dep_iata, "to": arr_iata})


def _extract_flights(data: dict) -> list[dict]:
    """Extract flight records from AviationStack response."""
    flights = []
    for f in data.get("data", []):
        flights.append({
            "flight": f.get("flight", {}).get("iata", "N/A"),
            "airline": f.get("airline", {}).get("name", "Unknown"),
            "dep_airport": f.get("departure", {}).get("airport", ""),
            "dep_iata": f.get("departure", {}).get("iata", ""),
            "dep_time": f.get("departure", {}).get("scheduled", ""),
            "arr_airport": f.get("arrival", {}).get("airport", ""),
            "arr_iata": f.get("arrival", {}).get("iata", ""),
            "arr_time": f.get("arrival", {}).get("scheduled", ""),
            "status": f.get("flight_status", "unknown"),
        })
    return flights


@tool
def book_flight(
    flight_id: Annotated[str, "Flight IATA code or ID to book"],
    passenger_name: Annotated[str, "Passenger full name"],
) -> str:
    """Book a specific flight for a passenger. Returns confirmation."""
    code = "BK-" + uuid.uuid4().hex[:8].upper()
    return (
        f"Flight {flight_id} booked for {passenger_name}.\n"
        f"Confirmation Code: {code}\n"
        f"E-ticket will be sent to the passenger's email."
    )


def create_agent(client):
    """Create the flight booking specialist agent."""
    instructions = INSTRUCTIONS.format(today=date_mod.today().isoformat())
    return Agent(
        client,
        instructions,
        name="flight_agent",
        description="Flight search and booking specialist using live schedule data.",
        tools=[search_flights, book_flight],
        require_per_service_call_history_persistence=True,
    )
