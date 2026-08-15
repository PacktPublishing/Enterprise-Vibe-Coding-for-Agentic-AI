"""
Shared infrastructure for all agents.

Provides the Azure OpenAI clients (text + image), credentials,
the background async event loop, and common utility functions
(image generation, JSON parsing).
"""

import asyncio
import base64
import json
import os
import re
import threading

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
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
# `azure_endpoint` MUST be the bare resource URL; strip any trailing
# `/openai/v1` (or `/openai`) so the SDK doesn't double-append and 404.
_endpoint = AZURE_OPENAI_ENDPOINT.rstrip("/")
for _suffix in ("/openai/v1", "/openai"):
    if _endpoint.endswith(_suffix):
        _endpoint = _endpoint[: -len(_suffix)]
        break
AZURE_OPENAI_ENDPOINT = _endpoint

DEPLOYMENT_NAME = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
IMAGE_DEPLOYMENT = os.environ.get("AZURE_OPENAI_IMAGE_DEPLOYMENT", "gpt-image-1.5")

# Directory for generated campaign images
IMAGES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "generated_images",
)
os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Credentials & Clients
# ---------------------------------------------------------------------------
# DefaultAzureCredential chains az-cli, env vars, managed identity, etc.
# Wrapping it in a bearer-token provider avoids the AzureCliCredential
# subprocess being re-invoked from background asyncio threads (which fails on
# Windows with "Failed to invoke the Azure CLI").
credential = DefaultAzureCredential()
_token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

client = OpenAIChatClient(
    model=DEPLOYMENT_NAME,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    credential=_token_provider,
)

image_client = OpenAI(
    base_url=f"{AZURE_OPENAI_ENDPOINT}/openai/v1/",
    api_key=_token_provider,
)

# ---------------------------------------------------------------------------
# Web-search tool — from the chat client itself (per Agent Framework docs)
# ---------------------------------------------------------------------------
try:
    web_search_tool = client.get_web_search_tool()
except Exception as _e:
    print(f"web_search_tool unavailable: {_e}")
    web_search_tool = None

# ---------------------------------------------------------------------------
# Shared async event loop  (runs in a background daemon thread)
# ---------------------------------------------------------------------------
_loop = asyncio.new_event_loop()


def _start_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=_start_loop, args=(_loop,), daemon=True).start()

# ---------------------------------------------------------------------------
# Image generation helper
# ---------------------------------------------------------------------------


def generate_campaign_image(prompt: str, size: str = "1024x1024") -> bytes:
    """Call gpt-image-1.5 and return raw PNG bytes."""
    result = image_client.images.generate(
        model=IMAGE_DEPLOYMENT,
        prompt=prompt,
        n=1,
        size=size,
    )
    return base64.b64decode(result.data[0].b64_json)


# ---------------------------------------------------------------------------
# JSON parsing helper
# ---------------------------------------------------------------------------
# NOTE: _repair_agent is set by __init__.py after agents are created,
# to avoid circular imports.  Falls back to raising if not set.
_repair_agent = None


def parse_agent_json(raw: str, agent_name: str = "agent") -> dict:
    """Attempt to parse JSON from agent output, handling common LLM quirks."""
    text = str(raw).strip()
    print(f"  [{agent_name}] Raw output ({len(text)} chars): {text[:200]}...")

    # Strip markdown code fences if present
    if "```" in text:
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

    # If text doesn't start with {, try to find the JSON object
    if not text.startswith("{"):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

    # Fix trailing commas before } or ] (common LLM mistake)
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Fix missing commas between key-value pairs
    text = re.sub(r'([}\]])\s*"', r'\1,"', text)
    text = re.sub(r'\{,', '{', text)
    text = re.sub(r'"\s*\{', '",{', text)
    if text.startswith('",'):
        text = text[2:]

    attempts = [
        lambda t: json.loads(t),
        lambda t: json.loads(re.sub(r"[\x00-\x1f\x7f]", " ", t)),
        lambda t: json.loads(
            re.sub(r",\s*([}\]])", r"\1", re.sub(r"[\x00-\x1f\x7f]", " ", t))
        ),
    ]

    last_err = None
    for attempt_fn in attempts:
        try:
            result = attempt_fn(text)
            print(f"  [{agent_name}] JSON parsed successfully")
            return result
        except json.JSONDecodeError as e:
            last_err = e
            continue

    # Final fallback: ask an agent to fix the JSON
    print(f"  [{agent_name}] All parse attempts failed: {last_err}")

    if _repair_agent is None:
        raise ValueError(f"JSON parsing failed for {agent_name}: {last_err}")

    print(f"  [{agent_name}] Attempting LLM-based JSON repair...")
    repair_prompt = (
        "The following text is supposed to be valid JSON but has syntax errors. "
        "Fix it and return ONLY the corrected JSON, nothing else:\n\n"
        f"{text[:3000]}"
    )
    repair_future = asyncio.run_coroutine_threadsafe(
        _repair_agent.run(repair_prompt), _loop
    )
    repaired = str(repair_future.result(timeout=30)).strip()

    if "```" in repaired:
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", repaired, re.DOTALL)
        if match:
            repaired = match.group(1).strip()

    if not repaired.startswith("{"):
        match = re.search(r"\{.*\}", repaired, re.DOTALL)
        if match:
            repaired = match.group(0)

    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
    return json.loads(repaired)
