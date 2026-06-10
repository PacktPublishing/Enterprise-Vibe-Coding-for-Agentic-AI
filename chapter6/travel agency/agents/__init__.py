"""
Agent Registry — creates all travel-agency agents at import time.
"""

from .client import client, _loop
from . import triage_agent, flight_agent, hotel_agent

# Create agents
triage = triage_agent.create_agent(client)
flights = flight_agent.create_agent(client)
hotels = hotel_agent.create_agent(client)
