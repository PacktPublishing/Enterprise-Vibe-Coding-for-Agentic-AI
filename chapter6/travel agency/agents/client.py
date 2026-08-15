"""
Shared Azure OpenAI client and background event loop for all agents.
"""

import asyncio
import os
import threading

from azure.identity import AzureCliCredential
from agent_framework.openai import OpenAIChatClient

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Configuration
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
if not AZURE_OPENAI_ENDPOINT:
    raise RuntimeError("AZURE_OPENAI_ENDPOINT must be set in the environment.")
# Defensive normalization — strip trailing /openai/v1 if present
_endpoint = AZURE_OPENAI_ENDPOINT.rstrip("/")
for _suffix in ("/openai/v1", "/openai"):
    if _endpoint.endswith(_suffix):
        _endpoint = _endpoint[: -len(_suffix)]
        break
AZURE_OPENAI_ENDPOINT = _endpoint

DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID")

# AviationStack API key (free tier)
AVIATIONSTACK_API_KEY = os.environ.get("AVIATIONSTACK_API_KEY", "")

# Credential
credential = (
    AzureCliCredential(tenant_id=AZURE_TENANT_ID)
    if AZURE_TENANT_ID
    else AzureCliCredential()
)

# Client
client = OpenAIChatClient(
    model=DEPLOYMENT_NAME,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    credential=credential,
)

# Background async event loop (daemon thread)
_loop = asyncio.new_event_loop()


def _start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=_start_loop, args=(_loop,), daemon=True, name="async-loop").start()
