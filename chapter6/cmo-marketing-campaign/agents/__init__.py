"""
Agent Registry — single import point for app.py.

Creates all agents at import time and exposes them, along with
shared infrastructure (clients, event loop, helpers).
"""

from .client import (                       # noqa: F401  — re-exported
    # Configuration
    AZURE_OPENAI_ENDPOINT,
    DEPLOYMENT_NAME,
    IMAGE_DEPLOYMENT,
    IMAGES_DIR,
    # Credentials & clients
    credential,
    client,
    image_client,
    web_search_tool,
    # Async event loop
    _loop,
    # Helpers
    generate_campaign_image,
    parse_agent_json,
)

# Agent modules
from . import (
    strategy,
    content,
    audience,
    performance,
    email_channel,
    instagram_channel,
    tiktok_channel,
    linkedin_channel,
)

# ---------------------------------------------------------------------------
# Create all agents (once at import time)
# ---------------------------------------------------------------------------
strategy_agent    = strategy.create_agent(client, tools=[web_search_tool] if web_search_tool else None)
content_agent     = content.create_agent(client)
audience_agent    = audience.create_agent(client)
performance_agent = performance.create_agent(client)

email_agent       = email_channel.create_agent(client)
instagram_agent   = instagram_channel.create_agent(client)
tiktok_agent      = tiktok_channel.create_agent(client)
linkedin_agent    = linkedin_channel.create_agent(client)

# Wire up the JSON-repair fallback agent (avoids circular import in client.py)
from . import client as _client_mod        # noqa: E402
_client_mod._repair_agent = strategy_agent

# ---------------------------------------------------------------------------
# Convenience look-up dicts
# ---------------------------------------------------------------------------
MAIN_AGENTS = {
    "strategy":    strategy_agent,
    "content":     content_agent,
    "audience":    audience_agent,
    "performance": performance_agent,
}

CHANNEL_AGENTS = {
    "email":     email_agent,
    "instagram": instagram_agent,
    "tiktok":    tiktok_agent,
    "linkedin":  linkedin_agent,
}

# Channels that need a generated image
IMAGE_CHANNELS = {"instagram", "tiktok"}
