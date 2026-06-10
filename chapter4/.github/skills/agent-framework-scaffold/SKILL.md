---
name: agent-framework-scaffold
description: "Scaffold and build multi-agent AI applications using Microsoft Agent Framework SDK with Azure OpenAI. USE FOR: create agent app, build multi-agent pipeline, scaffold agent project, add agents to Flask app, create AI-powered web app with agents, build agent orchestration, SSE streaming agents, create specialized agents. DO NOT USE FOR: deploy to Azure Foundry (use microsoft-foundry skill), manage Azure resources, general Python web apps without agents."
argument-hint: "Describe the domain, agents needed, and data sources for your app"
---

# Build Multi-Agent Apps with Microsoft Agent Framework

Create AI-powered applications with specialized agents orchestrated through a web interface, following the patterns proven in production agent apps.

## When to Use

- Building a new app that needs multiple AI agents working together
- Adding an agent pipeline to an existing project
- Creating specialized domain agents (analysis, comparison, synthesis)
- Setting up agent orchestration with real-time streaming UI

## Architecture Pattern

```
project/
├── app.py                    # Flask app with API routes and SSE streaming
├── requirements.txt          # Dependencies: flask, azure-identity, agent-framework
├── agents/
│   ├── __init__.py           # Agent registry — single import point
│   ├── client.py             # Shared Azure OpenAI client and config
│   ├── <domain>_agent.py     # One file per specialized agent
│   └── orchestrator_agent.py # Synthesis/executive agent
├── data/                     # Domain-specific data directories
│   └── <source>/
│       └── *.csv
└── templates/
    └── index.html            # Web UI with SSE progress tracking
```

## Procedure

### Step 1: Define the Agent Roster

Before writing code, identify the agents needed. Follow this pattern:

| Role | Purpose | Example |
|------|---------|---------|
| **Domain Analyst** (1-3) | Each analyzes one data source or dimension | Sales Agent, Feedback Agent |
| **Comparator** (0-1) | Cross-cuts data across dimensions | Route Comparison Agent |
| **Orchestrator** (1) | Synthesizes all agent outputs into executive view | Executive Copilot |

Ask the user:
- What domain is this for?
- What data sources exist (CSVs, APIs, databases)?
- What decisions should the app support?
- How many specialized perspectives are needed?

### Step 2: Create the Shared Client

Create `agents/client.py` with:

```python
import asyncio
import json
import os
import re
import subprocess
import threading

from azure.identity import AzureCliCredential
try:
    from agent_framework import HostedWebSearchTool
except ImportError:
    HostedWebSearchTool = None
from agent_framework.openai import OpenAIChatClient

# Configuration
AZURE_OPENAI_ENDPOINT = os.environ.get(
    'AZURE_OPENAI_ENDPOINT',
    "your-openai-endpoint"
)
# Defensive normalization — `azure_endpoint` MUST be the bare resource URL.
# Strip a trailing `/openai/v1` (or `/openai`) if a user supplied the full
# Azure portal URL by mistake; otherwise the SDK double-appends and 404s.
_endpoint = AZURE_OPENAI_ENDPOINT.rstrip('/')
for _suffix in ('/openai/v1', '/openai'):
    if _endpoint.endswith(_suffix):
        _endpoint = _endpoint[: -len(_suffix)]
        break
AZURE_OPENAI_ENDPOINT = _endpoint

DEPLOYMENT_NAME = os.environ.get('AZURE_OPENAI_DEPLOYMENT', 'gpt-4.1-mini')

# Azure AD tenant — pin so `az login` always targets the correct directory.
# Replace the placeholder below with your own tenant ID, or (preferred) set
# the AZURE_TENANT_ID environment variable so no real ID is committed.
AZURE_TENANT_ID = os.environ.get(
    'AZURE_TENANT_ID',
    '00000000-0000-0000-0000-000000000000',  # <your-tenant-id>
)

# Data directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
# Add domain-specific subdirectories as needed

# Client
credential = AzureCliCredential(tenant_id=AZURE_TENANT_ID)

# Ensure there is a valid Azure CLI session on the correct tenant; run `az login` if not
try:
    credential.get_token("https://cognitiveservices.azure.com/.default")
except Exception:
    print(f"No valid Azure CLI token for tenant {AZURE_TENANT_ID}. Running 'az login'...")
    subprocess.run(
        f"az login --tenant {AZURE_TENANT_ID}",
        check=True,
        shell=True,  # shell=True needed on Windows where az is a .cmd
    )
    credential = AzureCliCredential(tenant_id=AZURE_TENANT_ID)  # refresh after login

client = OpenAIChatClient(
    model=DEPLOYMENT_NAME,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    credential=credential,
)

# Web-search tool (optional; unavailable in some agent_framework versions)
if HostedWebSearchTool is not None:
    web_search_tool = HostedWebSearchTool(
        description="Search the web for current trends, data, and industry information.",
    )
else:
    web_search_tool = None

# Background async event loop (daemon thread)
_loop = asyncio.new_event_loop()

def _start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

threading.Thread(target=_start_loop, args=(_loop,), daemon=True).start()

# JSON parsing helper
def parse_agent_json(raw: str) -> dict:
    """Extract and parse JSON from agent response text."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {'error': 'Could not parse agent response', 'raw': raw}
```

Key decisions in this file:
- **`OpenAIChatClient`** — unified client for both OpenAI and Azure OpenAI; use `azure_endpoint` + `credential` for Azure, or `api_key` for plain OpenAI
- **`model`** parameter — maps to the Azure deployment name or OpenAI model name
- **`azure_endpoint`** must be the bare resource URL (e.g. `https://<name>.openai.azure.com`) — do NOT append `/openai/v1/`; the SDK adds the path automatically. If you need to override the full path, use `base_url` instead. The defensive normalization above strips a trailing `/openai/v1` if present so the wrong env var doesn't break startup.
- **AzureCliCredential** for local dev, pinned to `AZURE_TENANT_ID` so it always targets the right directory; swap to `DefaultAzureCredential` for production
- **Auto `az login --tenant <AZURE_TENANT_ID>`** — checks for a valid token at startup and runs `az login` against the configured tenant automatically if none is found
- **`web_search_tool`** — optional `HostedWebSearchTool` when available; otherwise set to `None`. Do not instantiate `SupportsWebSearchTool` directly (it is a protocol/interface)
- **Background event loop** lets synchronous Flask routes call async agents
- **`parse_agent_json`** handles LLM responses that wrap JSON in markdown code blocks

### Step 3: Create Each Specialized Agent

For each agent, create `agents/<name>_agent.py` following this template:

```python
"""
<Agent Name> — <One-line description of what it analyzes>.
"""

INSTRUCTIONS = """You are a <Role Name> for <domain>.
Your job is to <primary task>.

You will receive:
1. <Data source 1>
2. <Data source 2>

Analyze for:
1. **<Dimension 1>**: <What to look for>
2. **<Dimension 2>**: <What to look for>

Return ONLY valid JSON (no markdown, no extra text) with this exact structure:

{
    "summary": "<executive overview>",
    "<section_1>": [...],
    "<section_2>": [...],
    "actionable_recommendations": [
        {
            "priority": "high/medium/low",
            "area": "<category>",
            "title": "<short title>",
            "description": "<detail>",
            "estimated_impact": "<expected outcome>"
        }
    ]
}

<Quality instructions: be precise with numbers, focus on actionable insights, etc.>
"""


def create_agent(client, tools=None):
    """Create and return the <Agent Name>."""
    from agent_framework import Agent
    # NOTE (agent-framework >= 1.2): `client` and `instructions` are POSITIONAL.
    # Do NOT pass them as keyword arguments — there is no `client=` kwarg, and
    # do NOT call `create_agent()` on `OpenAIChatClient`; that method does not exist.
    # The legacy `ChatAgent` class no longer exists. Use `Agent` for everything.
    return Agent(
        client,
        INSTRUCTIONS,
        name='<AgentCamelCaseName>',
        tools=tools or [],
    )
```

**Rules for agent instructions:**
- Always request JSON-only output with an exact schema
- Include all field names and types in the schema example
- Be specific about what data the agent will receive
- End with quality directives (precision, actionability, audience)
- Keep instructions under ~2000 tokens for best results

### Step 4: Create the Agent Registry

Create `agents/__init__.py` to wire everything together:

```python
"""
Agent Registry — single import point for app.py.
"""
from .client import (
    DEPLOYMENT_NAME, DATA_DIR,
    credential, client, _loop, parse_agent_json,
    web_search_tool,
    # export all data directory constants
)

from . import (
    # import each agent module
)

# Create all agents once at import time
agent_1 = module_1.create_agent(client)
agent_2 = module_2.create_agent(client)
orchestrator = orchestrator_module.create_agent(client)
```

### Step 5: Build the Flask Orchestration

Create `app.py` with these patterns:

**Data loaders** — one function per data source:
```python
def _load_data(directory, filter_fn=None):
    """Load CSV files from a data directory."""
    results = {}
    if os.path.exists(directory):
        for fname in os.listdir(directory):
            if fname.endswith('.csv'):
                fpath = os.path.join(directory, fname)
                key = fname.replace('.csv', '')
                if filter_fn and not filter_fn(key):
                    continue
                with open(fpath, 'r', encoding='utf-8') as f:
                    results[key] = {'filename': fname, 'content': f.read()}
    return results
```

**Agent runner** — bridge sync Flask to async agents:
```python
def _run_agent(agent, prompt: str, session=None) -> str:
    async def _execute():
        # agent-framework >= 1.2: `run(stream=False)` returns an awaitable AgentResponse.
        response = await agent.run(prompt, session=session)
        return response.text if hasattr(response, 'text') else str(response)
    future = asyncio.run_coroutine_threadsafe(_execute(), _loop)
    return future.result(timeout=120)
```

**Conversational sessions** — use `agent.create_session(...)` to keep multi-turn memory:
```python
# One AgentSession per user/conversation; pass it on every `run(...)` call.
session = agent.create_session(session_id=user_session_id)
response = await agent.run("Hello!", session=session)
response = await agent.run("What did I just say?", session=session)  # remembers turn 1
```
There is no `get_new_thread()` / `AgentThread` anymore — sessions replace threads.

**SSE pipeline** — run agents sequentially with progress streaming:
```python
@app.route('/api/analyze', methods=['POST'])
def analyze():
    def _sse(payload):
        return f'data: {json.dumps(payload)}\n\n'

    def generate():
        results = {}

        # Stage 1: First agent
        yield _sse({'stage': 'agent_1', 'status': 'running', 'progress': 5})
        raw = _run_agent(agent_1, build_prompt_1(data))
        results['agent_1'] = parse_agent_json(raw)
        yield _sse({'stage': 'agent_1', 'status': 'complete', 'progress': 33, 'data': results['agent_1']})

        # Stage 2: Second agent
        # ...repeat pattern...

        # Final stage: Orchestrator synthesizes all results
        exec_prompt = f'Synthesize findings:\n{json.dumps(results, indent=2)}'
        raw = _run_agent(orchestrator, exec_prompt)
        results['orchestrator'] = parse_agent_json(raw)
        yield _sse({'stage': 'complete', 'progress': 100, 'data': results})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )
```

**Follow-up Q&A** — conversational endpoint using analysis context:
```python
@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get('question', '')
    # Include prior analysis results as context
    # Override orchestrator to respond in markdown (not JSON)
    prompt = f'User asks: "{question}"\nRespond in markdown, not JSON.\n\nContext:\n{context}'
    # Stream response via SSE
```

**Token streaming (chat UI)** — for conversational apps, stream tokens to the browser as they arrive. `agent.run(stream=True, ...)` returns a `ResponseStream` you iterate with `async for`; each `update.text` is a delta:

```python
import queue

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    data = request.get_json(force=True) or {}
    message = (data.get('message') or '').strip()
    session_id = data.get('session_id') or uuid.uuid4().hex
    session = _get_session(session_id)  # cached agent.create_session(session_id=...)

    # Bridge async -> sync generator via a thread-safe queue.
    q: "queue.Queue[tuple[str, str]]" = queue.Queue()

    async def _produce():
        try:
            stream = chat_agent.run(message, stream=True, session=session)
            async for update in stream:
                delta = getattr(update, 'text', '') or ''
                if delta:
                    q.put(('delta', delta))
            q.put(('done', ''))
        except Exception as exc:
            q.put(('error', str(exc)))

    asyncio.run_coroutine_threadsafe(_produce(), _loop)

    def _sse(event, payload):
        return f'event: {event}\ndata: {json.dumps(payload)}\n\n'

    def generate():
        yield _sse('session', {'session_id': session_id})
        while True:
            kind, value = q.get()
            if kind == 'delta':
                yield _sse('delta', {'text': value})
            elif kind == 'done':
                yield _sse('done', {}); break
            elif kind == 'error':
                yield _sse('error', {'message': value}); break

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'},
    )
```

On the browser side, parse SSE manually (the native `EventSource` API does not support `POST`); read `response.body.getReader()`, split chunks on `\n\n`, and parse `event:` / `data:` lines.

### Step 6: Set Up Dependencies

Create `requirements.txt`:
```
flask
azure-identity
agent-framework
```

### Step 7: Verify the Build

Run these checks:
1. `pip install -r requirements.txt` — dependencies install cleanly
2. `python -c "from agents import client"` — client initializes without error
3. `python app.py` — Flask starts and serves the UI
4. Test the `/api/analyze` (or `/api/chat`) endpoint — SSE events stream correctly

## API Cheatsheet (agent-framework >= 1.2)

| Task | Correct API | Common mistakes |
|------|-------------|-----------------|
| Build agent | `Agent(client, INSTRUCTIONS, name=..., tools=[...])` | Calling `OpenAIChatClient.create_agent(...)`; passing `client=...` as kwarg; using `ChatAgent` (removed); using `chat_client=...` |
| One-shot run | `await agent.run(prompt, session=session)` → `AgentResponse` (use `.text`) | Expecting a string directly |
| Stream tokens | `agent.run(prompt, stream=True, session=session)` → `ResponseStream`; `async for update in stream: update.text` | Using `agent.run_stream(...)` (doesn't exist); awaiting the stream |
| Multi-turn memory | `session = agent.create_session(session_id=...)` then pass `session=` to every `run()` | Using `agent.get_new_thread()` / `AgentThread` (removed) |
| Azure endpoint | `azure_endpoint="https://<name>.openai.azure.com"` | Appending `/openai/v1/` — SDK adds the path itself, produces 404 |
| Deployment name | `model='gpt-4.1-mini'` (your Azure *deployment* name) | Using OpenAI public model id when the deployment is named differently |
| Credential | `AzureCliCredential(tenant_id=AZURE_TENANT_ID)` | Default `AzureCliCredential()` — may pick wrong tenant |

## Design Principles

1. **One agent per file** — keeps instructions focused and testable
2. **JSON-only agent output** — structured responses enable UI rendering and downstream agent consumption
3. **Registry pattern** — `__init__.py` creates agents once at import; app.py never touches agent internals
4. **Sequential pipeline** — later agents consume earlier agents' outputs for richer synthesis
5. **SSE streaming** — users see real-time progress as each agent completes
6. **Background event loop** — single daemon thread bridges sync Flask with async agent SDK
7. **Robust JSON parsing** — `parse_agent_json` handles LLMs wrapping JSON in markdown code blocks

## Common Variations

| Need | Approach |
|------|----------|
| Add tools to agents | Pass tool definitions in `create_agent(client, tools=[...])` |
| Parallel agents | Use `asyncio.gather` in the event loop instead of sequential `_run_agent` |
| Non-Flask framework | Replace Flask SSE with FastAPI `StreamingResponse` or similar |
| File uploads | Add upload route, save to `data/`, then include in agent prompts |
| Chat memory | Store conversation history per session, prepend to orchestrator prompt |

## Available Tools Reference

Besides web-search tooling (configured in `client.py` when available), the Agent Framework provides several additional tool types you can initialize and pass to agents. All examples below use `OpenAIChatClient` as the client, consistent with the shared client setup.

### 1. Function Tools

Turn any Python function into a tool by passing it directly to an agent's `tools` parameter. Use `Annotated` + Pydantic `Field` for parameter descriptions, and the `@tool` decorator for explicit name/description:

```python
from typing import Annotated
from pydantic import Field
from agent_framework import tool

@tool(name="get_weather", description="Get current weather for a location.")
def get_weather(
    location: Annotated[str, Field(description="The city name to get weather for.")],
) -> str:
    """Get the weather for a given location."""
    return f"The weather in {location} is cloudy with a high of 15°C."
```

Pass it when creating the agent:

```python
def create_agent(client, tools=None):
    from agent_framework import Agent
    return Agent(
        client,
        INSTRUCTIONS,
        name='WeatherAgent',
        tools=[get_weather] + (tools or []),
    )
```

**Class-based tools** — when multiple tools share state, wrap them in a class and pass bound methods:

```python
from agent_framework import tool

class DataTools:
    def __init__(self, db_connection):
        self.db = db_connection

    def query_sales(
        self,
        region: Annotated[str, "Sales region to query"],
    ) -> str:
        """Query sales data for a region."""
        return self.db.execute(f"SELECT * FROM sales WHERE region='{region}'")

    def query_inventory(
        self,
        product: Annotated[str, "Product name"],
    ) -> str:
        """Query inventory levels."""
        return self.db.execute(f"SELECT * FROM inventory WHERE product='{product}'")

# Usage
tools = DataTools(db_connection)
from agent_framework import Agent
agent = Agent(
    client,
    INSTRUCTIONS,
    name='DataAgent',
    tools=[tools.query_sales, tool(description="Check inventory")(tools.query_inventory)],
)
```

**Runtime context** — use `FunctionInvocationContext` for per-invocation values (user ID, session) that the model should NOT see in the schema:

```python
from agent_framework import FunctionInvocationContext, tool

@tool(approval_mode="never_require")
def get_user_data(
    query: Annotated[str, Field(description="What to look up")],
    ctx: FunctionInvocationContext,
) -> str:
    """Fetch user-specific data."""
    user_id = ctx.kwargs.get("user_id", "unknown")
    return f"Data for user {user_id}: ..."

# When running the agent, inject the context:
response = await agent.run(
    "Look up my recent orders",
    function_invocation_kwargs={"user_id": "user_123"},
)
```

### 2. Code Interpreter

Lets agents write and execute Python code in a sandboxed environment — useful for data analysis, math, and file processing. Obtain the tool from the client instance:

```python
# In client.py — initialize alongside other tools
# Note: get_code_interpreter_tool() is available on the client instance
code_interpreter_tool = client.get_code_interpreter_tool()
```

Pass it to an agent:

```python
def create_agent(client, tools=None):
    from .client import code_interpreter_tool
    from agent_framework import Agent
    return Agent(
        client,
        "You can write and execute Python code to analyze data.",
        name='AnalyticsAgent',
        tools=[code_interpreter_tool] + (tools or []),
    )
```

> **Note:** Code Interpreter availability depends on the underlying provider. See [Providers Overview](https://learn.microsoft.com/en-us/agent-framework/agents/providers/).

### 3. File Search

Enables agents to search through uploaded documents via vector stores — ideal for RAG-style Q&A over files:

```python
# 1. Upload a file and create a vector store (one-time setup)
async def setup_file_search(client):
    file = await client.client.files.create(
        file=("knowledge.txt", open("data/knowledge.txt", "rb")),
        purpose="user_data",
    )
    vector_store = await client.client.vector_stores.create(
        name="knowledge_base",
        expires_after={"anchor": "last_active_at", "days": 7},
    )
    await client.client.vector_stores.files.create_and_poll(
        vector_store_id=vector_store.id, file_id=file.id,
    )
    return vector_store.id

# 2. Create the file search tool
file_search_tool = client.get_file_search_tool(vector_store_ids=[vector_store_id])

# 3. Pass it to an agent
from agent_framework import Agent
agent = Agent(
    client,
    "Search through uploaded documents to answer questions.",
    name='DocSearchAgent',
    tools=[file_search_tool],
)
```

> **Note:** File Search availability depends on the underlying provider. See [Providers Overview](https://learn.microsoft.com/en-us/agent-framework/agents/providers/).

### 4. Local MCP Tools (Stdio, HTTP, WebSocket)

Connect to external MCP servers for additional capabilities. Three transport types are available:

Install the MCP dependency first (if not already present):
```
pip install mcp --pre
```
For WebSocket support add: `pip install "mcp[ws] --pre"`

**MCPStdioTool** — local MCP server running as a subprocess:

```python
from agent_framework import Agent, MCPStdioTool

async def run_with_local_mcp():
    async with (
        MCPStdioTool(
            name="calculator",
            command="uvx",
            args=["mcp-server-calculator"],
        ) as mcp_server,
        Agent(
            client,  # OpenAIChatClient from client.py
            "You solve calculations using the calculator tool.",
            name="MathAgent",
        ) as agent,
    ):
        result = await agent.run("What is 15 * 23 + 45?", tools=mcp_server)
        print(result)
```

**MCPStreamableHTTPTool** — remote MCP server over HTTP/SSE:

```python
from agent_framework import Agent, MCPStreamableHTTPTool

async def run_with_http_mcp():
    async with (
        MCPStreamableHTTPTool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
        ) as mcp_server,
        Agent(
            client,  # OpenAIChatClient from client.py
            "You help with Microsoft documentation questions.",
            name="DocsAgent",
        ) as agent,
    ):
        result = await agent.run(
            "How to create an Azure storage account using az cli?",
            tools=mcp_server,
        )
        print(result)
```

For authenticated HTTP endpoints, use `header_provider` with `function_invocation_kwargs` so secrets stay in runtime context:

```python
MCPStreamableHTTPTool(
    name="Authenticated MCP",
    url="https://api.example.com/mcp",
    header_provider=lambda kwargs: {"Authorization": f"Bearer {kwargs['api_key']}"},
)
# Then at run time:
result = await agent.run(prompt, function_invocation_kwargs={"api_key": os.getenv("API_KEY")})
```

**MCPWebsocketTool** — remote MCP server over WebSocket:

```python
from agent_framework import Agent, MCPWebsocketTool

async def run_with_ws_mcp():
    async with (
        MCPWebsocketTool(
            name="realtime-data",
            url="wss://api.example.com/mcp",
        ) as mcp_server,
        Agent(
            client,  # OpenAIChatClient from client.py
            "You provide real-time data insights.",
            name="DataAgent",
        ) as agent,
    ):
        result = await agent.run("What is the current market status?", tools=mcp_server)
        print(result)
```

Common local MCP servers:
| Server | Command | Purpose |
|--------|---------|---------|
| Calculator | `uvx mcp-server-calculator` | Math computations |
| Filesystem | `uvx mcp-server-filesystem` | File system operations |
| GitHub | `npx @modelcontextprotocol/server-github` | Repository access |
| SQLite | `uvx mcp-server-sqlite` | Database operations |

### 5. Hosted MCP Tools (Foundry)

When using **Microsoft Foundry** as the backend (via `FoundryChatClient`), MCP servers are hosted and managed by Foundry — no local infrastructure needed:

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

async def foundry_mcp_example():
    async with AzureCliCredential(tenant_id="<your-tenant-id>") as credential:
        foundry_client = FoundryChatClient(credential=credential)

        learn_mcp = foundry_client.get_mcp_tool(
            name="Microsoft Learn MCP",
            url="https://learn.microsoft.com/api/mcp",
        )

        async with Agent(
            foundry_client,
            "Answer questions using Microsoft Learn content.",
            name="LearnAgent",
            tools=[learn_mcp],
        ) as agent:
            result = await agent.run("Summarize the Azure AI Agent docs on MCP.")
            print(result.text)
```

Multiple hosted MCP tools with different approval modes:

```python
learn_mcp = foundry_client.get_mcp_tool(
    name="Microsoft Learn MCP",
    url="https://learn.microsoft.com/api/mcp",
    approval_mode="never_require",
)
github_mcp = foundry_client.get_mcp_tool(
    name="GitHub MCP",
    url="https://api.githubcopilot.com/mcp/",
    approval_mode="always_require",
    headers={"Authorization": f"Bearer {os.getenv('GITHUB_PAT')}"},
)

async with Agent(
    foundry_client,
    "Search docs and access GitHub repos.",
    name="MultiToolAgent",
    tools=[learn_mcp, github_mcp],
) as agent:
    result = await agent.run("Find Azure docs and check latest commits.")
```

> **Note:** Hosted MCP tools require a Foundry project endpoint. Set `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` environment variables.

### Tools Quick Reference

| Tool | Import / Init | When to Use |
|------|--------------|-------------|
| **Web Search** | `HostedWebSearchTool(...)` when import succeeds; otherwise `None` | Live web data, trends, competitor info |
| **Function Tool** | Any Python function or `@tool` decorated | Custom domain logic, API calls, DB queries |
| **Code Interpreter** | `client.get_code_interpreter_tool()` | Data analysis, math, file processing |
| **File Search** | `client.get_file_search_tool(vector_store_ids=[...])` | RAG over uploaded documents |
| **Local MCP (Stdio)** | `MCPStdioTool(name=..., command=..., args=[...])` | Local subprocess tools (calculator, filesystem) |
| **Local MCP (HTTP)** | `MCPStreamableHTTPTool(name=..., url=...)` | Remote MCP servers over HTTP/SSE |
| **Local MCP (WebSocket)** | `MCPWebsocketTool(name=..., url=...)` | Real-time MCP servers over WebSocket |
| **Hosted MCP (Foundry)** | `foundry_client.get_mcp_tool(name=..., url=...)` | Foundry-managed MCP servers (no infra) |
