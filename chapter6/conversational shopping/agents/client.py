"""
Shared infrastructure for the conversational shopping agents.

Provides the Azure OpenAI clients, credentials,
the background async event loop, and the image generation helper.
"""

import asyncio
import base64
import json
import os
import re
import threading

from azure.identity import AzureCliCredential, DefaultAzureCredential, get_bearer_token_provider
from agent_framework.openai import OpenAIChatClient
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
if not AZURE_OPENAI_ENDPOINT:
    raise RuntimeError("AZURE_OPENAI_ENDPOINT must be set in the environment.")
# Defensive normalization — `endpoint` must be the bare resource URL.
# Strip a trailing `/openai/v1` (or `/openai`) so the SDK doesn't double-append.
_endpoint = AZURE_OPENAI_ENDPOINT.rstrip("/")
for _suffix in ("/openai/v1", "/openai"):
    if _endpoint.endswith(_suffix):
        _endpoint = _endpoint[: -len(_suffix)]
        break
AZURE_OPENAI_ENDPOINT = _endpoint

DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
IMAGE_DEPLOYMENT = os.environ.get("AZURE_OPENAI_IMAGE_DEPLOYMENT", "gpt-image-1.5")

IMAGES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "generated_images",
)
os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Credentials & Clients
# ---------------------------------------------------------------------------
credential = AzureCliCredential()

client = OpenAIChatClient(
    model=DEPLOYMENT_NAME,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    credential=credential,
)

_image_token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
image_client = OpenAI(
    base_url=AZURE_OPENAI_ENDPOINT,
    api_key=_image_token_provider,
)

# ---------------------------------------------------------------------------
# Shared async event loop (runs in a background daemon thread)
# ---------------------------------------------------------------------------
_loop = asyncio.new_event_loop()


def _start_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=_start_loop, args=(_loop,), daemon=True).start()

# ---------------------------------------------------------------------------
# Image generation helper
# ---------------------------------------------------------------------------


def generate_product_image(prompt: str, size: str = "1024x1024") -> bytes:
    """Call gpt-image and return raw PNG bytes."""
    result = image_client.images.generate(
        model=IMAGE_DEPLOYMENT,
        prompt=prompt,
        n=1,
        size=size,
    )
    return base64.b64decode(result.data[0].b64_json)
