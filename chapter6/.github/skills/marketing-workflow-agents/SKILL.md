---
name: marketing-workflow-agents
description: 'Scaffold a new marketing-campaign capability inside `cmo-marketing-campaign/` using the team''s standard MAF patterns: content-generation agents, sequential pipelines, channel adapters (email / Instagram / TikTok / LinkedIn / new channels), localization flows, audit logging, and human approval gates. USE FOR: add a new pipeline stage, add a new marketing channel, add a localization step, add an approval / review gate, add audit logging to an agent run, refactor an ad-hoc agent into the standard registry pattern, scaffold a brand-safety reviewer, build a translator agent, build an A/B variant generator. DO NOT USE FOR: choosing between MAF orchestration patterns from scratch (use `maf-orchestration-patterns` first), Flask/SSE plumbing changes unrelated to agents, building the travel-agency or conversational-shopping apps, deploying to Foundry.'
---

# Marketing Workflow Agents

Team-standard playbook for adding capabilities to the **CMO marketing campaign app** (`cmo-marketing-campaign/`). It locks in the conventions the existing pipeline already uses (strategy → content → visual → audience → performance + per-channel adapters) so every new agent — a new channel, an approval gate, a localizer, an audit hook — drops in the same way.

If you have not yet picked the orchestration shape (sequential vs handoff vs group chat …), **first run [`maf-orchestration-patterns`](../maf-orchestration-patterns/SKILL.md)**. This skill assumes the answer for marketing pipelines is almost always **Sequential** (content generation → channel adaptation), with optional **Group Chat** for approval loops.

## House conventions (do not deviate)

Every agent in this app obeys these rules. Match them or the registry / pipeline breaks.

1. **One agent per file** under `cmo-marketing-campaign/agents/<name>.py`.
2. The file exports exactly two top-level symbols:
   - `INSTRUCTIONS: str` — system prompt. Always ends with a `Return ONLY valid JSON ...` clause and a literal JSON schema.
   - `create_agent(client, tools=None) -> Agent` — factory that returns `agent_framework.Agent(client, INSTRUCTIONS, name="...", tools=tools or [])`.
3. **Strict JSON output, always.** Pipeline code calls `parse_agent_json(raw, "<agent_name>")` from `agents/client.py`, which already handles fences, trailing commas, and LLM-based repair. Never invent a free-text agent.
4. **Register the agent in `agents/__init__.py`** — import the module, build the instance, and add it to the right look-up dict (`MAIN_AGENTS`, `CHANNEL_AGENTS`, or a new one you create).
5. **Drive runs through the shared loop**: `asyncio.run_coroutine_threadsafe(agent.run(prompt), _loop).result(timeout=…)`. Do *not* call `asyncio.run()` from request handlers.
6. **Stream progress over SSE** from `app.py` with the three event shapes already in use: `agent_start`, `agent_complete`, `agent_error`, plus `log` entries. Every new stage must emit all four.
7. **Web search is gated on `web_search_tool`** in `client.py` — if `None`, pass `tools=[]` and instruct the agent to work from given context only.
8. **Images** go through `generate_campaign_image(prompt, size=...)` and are saved under `IMAGES_DIR`. Channels that need an image must be added to `IMAGE_CHANNELS`.

## Decision flow — what kind of capability am I adding?

Walk in order, stop at the first match.

1. **A new step that produces something downstream needs** (e.g. a "competitive_intel" agent feeding strategy) → **New main pipeline agent**. Insert as a new section in `app.py`'s `generate()` generator, add to `MAIN_AGENTS`. Follow §1.
2. **A new place the campaign gets published** (Reddit, Pinterest, X, podcast script, SMS …) → **New channel adapter**. Add to `CHANNEL_AGENTS`. Follow §2.
3. **A new language / region variant of an existing channel** → **Localization adapter**. Wraps an existing channel agent, does not replace it. Follow §3.
4. **A required sign-off before content can leave the pipeline** (brand safety, legal, CMO) → **Approval gate**. Either a reviewer agent in a group-chat loop, or a deterministic gate emitted as an SSE event awaiting a UI ack. Follow §4.
5. **Compliance / replay requirement** ("we need to know who said what, when, with which tools") → **Audit logging**. Cross-cutting; wrap the agent run. Follow §5.
6. **Same agents, different shape** (e.g. "generate three variants in parallel") → go back to `maf-orchestration-patterns` and choose Concurrent or Group Chat. Do not invent a new orchestrator here.

---

## §1 — Scaffold: New main pipeline agent

Use when the agent produces structured data that *later* agents will consume (like `strategy_data` → `content_agent`).

**Files to touch**

| File | Change |
|---|---|
| `cmo-marketing-campaign/agents/<name>.py` | New — INSTRUCTIONS + `create_agent` |
| `cmo-marketing-campaign/agents/__init__.py` | Import module, build agent, add to `MAIN_AGENTS` |
| `cmo-marketing-campaign/app.py` | New numbered section in `generate()`, between the right two existing stages |

**Agent template** (`agents/<name>.py`):

```python
"""
<Name> Agent — <one-line role>.
"""

INSTRUCTIONS = """You are a Marketing <Name> Agent. Your job is to <single responsibility>.

Given <inputs the upstream stages will provide>, you MUST return ONLY valid JSON (no markdown, no extra text) with this exact structure:

{
    "<field_1>": "<description>",
    "<field_2>": ["<item>", "<item>"]
}

<Tone / constraints / dos and don'ts. Reference concrete metrics or upstream
fields by name so the model knows to ground in them.>"""


def create_agent(client, tools=None):
    """Create and return the <Name> Agent."""
    from agent_framework import Agent
    return Agent(
        client,
        INSTRUCTIONS,
        name="<Name>Agent",
        tools=tools or [],
    )
```

**Pipeline section template** (paste into `app.py`'s `generate()`, in pipeline order):

```python
# ===================================================================
# N. <Name> Agent
# ===================================================================
yield "data: " + json.dumps({"type": "agent_start", "agent": "<name>", "time": _timestamp()}) + "\n\n"
yield "data: " + json.dumps({"type": "log", "time": _timestamp(),
    "text": "<Name> Agent activated - <verb>...", "color": "<name>"}) + "\n\n"

try:
    <name>_prompt = (
        f"<task line>:\n\n{brief}\n\n"
        f"Strategic context: {json.dumps(strategy_data)}\n\n"   # include upstream JSON
        "Return ONLY valid JSON."
    )
    future = asyncio.run_coroutine_threadsafe(<name>_agent.run(<name>_prompt), _loop)
    raw = future.result(timeout=60)
    <name>_data = _parse_agent_json(str(raw), "<name>")
    results["<name>"] = <name>_data

    yield "data: " + json.dumps({"type": "agent_complete", "agent": "<name>",
        "data": <name>_data, "time": _timestamp()}) + "\n\n"
    yield "data: " + json.dumps({"type": "log", "time": _timestamp(),
        "text": "<Name> Agent completed - <outcome>", "color": "default"}) + "\n\n"

except Exception as e:
    yield "data: " + json.dumps({"type": "agent_error", "agent": "<name>", "error": str(e)}) + "\n\n"
    yield "data: " + json.dumps({"type": "done"}) + "\n\n"
    return
```

**Registry edit** (`agents/__init__.py`):

```python
from . import <name>                              # add to module imports
<name>_agent = <name>.create_agent(client)         # add to "Create all agents"

MAIN_AGENTS = {                                    # add to the dict
    ...
    "<name>": <name>_agent,
}
```

Also re-export `<name>_agent` from the registry's import list in `app.py`.

---

## §2 — Scaffold: New channel adapter

A channel adapter takes the **whole** completed campaign and reshapes it for one publishing surface. It must NOT call upstream agents itself — keep adapters pure transforms of the result bundle.

**Files to touch**

| File | Change |
|---|---|
| `agents/<channel>_channel.py` | New — INSTRUCTIONS + `create_agent` |
| `agents/__init__.py` | Build agent, add to `CHANNEL_AGENTS`, optionally to `IMAGE_CHANNELS` |
| `app.py` | If the channel is invoked from a new endpoint, follow the same SSE pattern as existing channels (see how `email_agent` is wired) |

**Channel template** — copy the JSON-schema discipline from [`email_channel.py`](../../../cmo-marketing-campaign/agents/email_channel.py) or [`linkedin_channel.py`](../../../cmo-marketing-campaign/agents/linkedin_channel.py):

```python
"""
<Channel> Channel Agent — Adapts campaign content for <surface>.
"""

INSTRUCTIONS = """You are a <Channel> Marketing Agent. Your job is to adapt a completed marketing campaign for <surface>.

Given the full campaign data (strategy, content, audience, performance), produce <channel>-optimised content.

Return ONLY valid JSON (no markdown, no extra text) with this exact structure:

{
    "<field_1>": "<channel-native shape, length limits, format hints>",
    ...
}

Best practices:
- <2-4 platform-specific rules: char limits, tone, format conventions, hashtag policy>
"""


def create_agent(client, tools=None):
    from agent_framework import Agent
    return Agent(client, INSTRUCTIONS, name="<Channel>Agent", tools=tools or [])
```

**Channel checklist (must all be true before merging):**

- [ ] JSON schema fields match the channel's native constraints (subject ≤ 60 chars for email, ≤ 280 chars for X posts, etc.).
- [ ] Agent is referenced via `CHANNEL_AGENTS["<channel>"]` (no direct symbol use in app.py).
- [ ] If the channel renders an image, the channel name is in `IMAGE_CHANNELS` *and* the prompt sent to `generate_campaign_image` uses `content_data["primary_headline"]` + `tone`.
- [ ] No upstream pipeline call — adapter receives `results` dict only.

---

## §3 — Scaffold: Localization flow

Localization wraps an existing channel (or content) agent. It runs **after** the source-language adapter and produces a same-shape JSON in the target locale, so the front-end can switch on locale without schema changes.

**Pattern: localizer = translator + brand-safety pass, NOT a full re-author.**

```python
# agents/localizer.py
"""
Localization Agent — Translates and culturally adapts channel output.
"""

INSTRUCTIONS = """You are a Localization Agent for marketing content.

You will receive:
  - "source_json": a channel-adapter output (e.g. an email or LinkedIn post JSON)
  - "target_locale": IETF tag (e.g. "fr-FR", "ja-JP", "pt-BR")
  - "region_notes": optional cultural / regulatory caveats

You MUST:
  1. Translate every string value to the target locale.
  2. Preserve the JSON structure EXACTLY — same keys, same nesting, same types.
  3. Adapt idioms, units, currency symbols, and dates to the target locale.
  4. Keep brand names, product names, and URLs verbatim.
  5. Respect character limits implied by the source field names
     (e.g. a 60-char subject line stays ≤ 60 chars after translation).

Return ONLY the localized JSON object. No commentary, no markdown."""


def create_agent(client, tools=None):
    from agent_framework import Agent
    return Agent(client, INSTRUCTIONS, name="LocalizerAgent", tools=tools or [])
```

**Wiring** — call once per (channel, locale) pair:

```python
async def _localize(channel_json: dict, locale: str) -> dict:
    prompt = json.dumps({
        "source_json": channel_json,
        "target_locale": locale,
        "region_notes": REGION_NOTES.get(locale, ""),
    })
    raw = await localizer_agent.run(prompt)
    return _parse_agent_json(str(raw), f"localizer:{locale}")
```

Localized outputs go into `results["<channel>"]["localizations"][locale]` — **never** overwrite the source-language version.

---

## §4 — Scaffold: Human approval gate

Two flavors. Pick by who must approve.

### 4a — Agent reviewer (automated brand / legal check)

Use a deterministic reviewer agent in a short **group-chat loop** with the producer. Cap iterations to avoid runaway costs.

```python
# agents/brand_reviewer.py
INSTRUCTIONS = """You are a Brand Safety Reviewer. You receive marketing JSON and decide if it is publishable.

Return ONLY valid JSON:

{
    "verdict": "approve" | "revise",
    "issues": ["<short, actionable issue>", ...],
    "score": 0-100
}

Approve only if there are zero blocking issues. Blocking issues include:
  - Unsubstantiated claims ("#1", "guaranteed")
  - Competitor names without context
  - Health/financial claims requiring disclaimers
  - Tone mismatch with brand guidelines (premium, factual, inclusive)
"""
```

**Loop pattern in `app.py`** (sequential, max 2 revisions):

```python
content_data = await_first_draft(...)
for attempt in range(2):
    review = _parse_agent_json(str(future_for(brand_reviewer_agent, content_data).result(60)), "brand_review")
    yield sse_log(f"Brand review attempt {attempt+1}: {review['verdict']} ({review['score']}/100)", "review")
    if review["verdict"] == "approve":
        break
    revise_prompt = f"Revise based on these issues: {review['issues']}\n\nOriginal:\n{json.dumps(content_data)}"
    content_data = _parse_agent_json(str(future_for(content_agent, revise_prompt).result(60)), "content")
results["content"] = content_data
results["content_review"] = review
```

### 4b — Human approval gate (CMO sign-off)

The pipeline **pauses**, the UI shows the artifact, the human clicks approve/reject. Implement as:

1. Emit an SSE event `{"type": "approval_required", "stage": "content", "data": content_data, "approval_id": <uuid>}` and **return early** from the generator. Store the in-flight `results` in a server-side dict keyed by `approval_id` (use `app.config["pending_approvals"]`).
2. New endpoint `POST /approve/<approval_id>` accepts `{"decision": "approve|reject", "feedback": "..."}`. On approve, the pipeline resumes via a continuation route `/generate/resume/<approval_id>` that picks up the stored results and emits the remaining stages.
3. On reject, emit `{"type": "approval_rejected", ...}` and discard the pending state.

Never block the SSE generator on a blocking `input()` or `time.sleep` — it will tie up the worker.

**Audit requirement:** every approval decision MUST also flow through §5.

---

## §5 — Scaffold: Audit logging

Every agent invocation must be observable: prompt, response, tool calls, latency, approver decision. Implement as a thin wrapper, **not** as logic baked into each agent.

```python
# agents/audit.py
import json, time, uuid, os
from datetime import datetime, timezone

AUDIT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_logs")
os.makedirs(AUDIT_DIR, exist_ok=True)


async def run_audited(agent, prompt: str, *, stage: str, run_id: str, options: dict | None = None):
    """Wrap agent.run with structured audit logging. Returns the raw response."""
    started = time.time()
    record = {
        "run_id": run_id,
        "stage": stage,
        "agent": getattr(agent, "name", agent.__class__.__name__),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
    }
    try:
        response = await agent.run(prompt, options=options or {})
        record["status"] = "ok"
        record["response_text"] = str(response)
        # Capture tool usage if present
        try:
            d = response.to_dict()
            tools = []
            for msg in d.get("messages", []):
                for c in msg.get("contents", []):
                    if c.get("type") == "function_call":
                        tools.append({"name": c.get("function_name"), "args": c.get("arguments")})
            record["tool_calls"] = tools
        except Exception:
            pass
        return response
    except Exception as e:
        record["status"] = "error"
        record["error"] = repr(e)
        raise
    finally:
        record["latency_ms"] = int((time.time() - started) * 1000)
        _append(record)


def _append(record: dict) -> None:
    """One JSONL file per run_id. Append-only."""
    path = os.path.join(AUDIT_DIR, f"{record['run_id']}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_event(run_id: str, event_type: str, payload: dict) -> None:
    """Audit non-agent events (approvals, gate decisions, errors)."""
    _append({
        "run_id": run_id,
        "stage": event_type,
        "ts": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    })
```

**Wiring rules:**

- Every `/generate` request mints a `run_id = uuid.uuid4().hex` at the top, includes it in every SSE event (`"run_id": run_id`), and threads it into every `run_audited(...)` call.
- Replace direct `asyncio.run_coroutine_threadsafe(agent.run(...), _loop)` with `run_audited(agent, prompt, stage=..., run_id=...)` scheduled on `_loop`.
- Approval decisions call `log_event(run_id, "approval", {...})`.
- Audit files are append-only JSONL; never mutate past records.

---

## Quality checklist — before opening the PR

- [ ] Agent file follows the two-symbol contract (`INSTRUCTIONS`, `create_agent`).
- [ ] Output is strict JSON with a literal schema in the prompt.
- [ ] Agent is registered in `agents/__init__.py` and exposed in the right look-up dict.
- [ ] Pipeline stage emits all four SSE shapes (`agent_start`, `log`, `agent_complete`, `agent_error`).
- [ ] All agent calls go through the shared `_loop` via `run_coroutine_threadsafe`.
- [ ] If web search is needed, the agent gracefully handles `web_search_tool is None`.
- [ ] If approval is needed, the SSE generator returns early and a resume endpoint exists.
- [ ] Every new code path is wrapped in `run_audited(...)` and the `run_id` is propagated.
- [ ] Localization (if any) preserves the source-language output under `results[channel]` and writes locales under `results[channel]["localizations"]`.
- [ ] No new global state. No `asyncio.run()` outside `_loop`. No `print` debugging left in `app.py` (use SSE `log` events).

## Anti-patterns (rejected in review)

- A channel agent that calls upstream agents itself.
- Free-text output that the caller `re.search`es. Use JSON + `_parse_agent_json`.
- A new `asyncio.new_event_loop()` per request.
- A localization agent that re-authors instead of translating (changes the JSON shape).
- Approval gates implemented as `time.sleep` / busy-wait inside the SSE generator.
- Audit logs scattered across `print` statements or per-agent ad-hoc files.
- An "uber-agent" with a 2000-line prompt that does strategy + content + channel in one go. Split it.

## Worked example — adding a Reddit channel with French localization, brand-safety gate, and audit

1. Create `agents/reddit_channel.py` per §2 (fields: `subreddit`, `post_title`, `post_body_markdown`, `flair`, `disclaimer`).
2. Register `reddit_agent` in `agents/__init__.py`; add `"reddit": reddit_agent` to `CHANNEL_AGENTS`.
3. Create `agents/localizer.py` per §3 if not already present.
4. Create `agents/brand_reviewer.py` per §4a.
5. Create `agents/audit.py` per §5.
6. In `app.py`'s channel-rendering endpoint:
   - Mint `run_id`.
   - Run `reddit_agent` via `run_audited(..., stage="reddit", run_id=run_id)`.
   - Loop `brand_reviewer_agent` up to 2× via §4a.
   - Run `localizer_agent` with `target_locale="fr-FR"` per §3.
   - Stash result under `results["reddit"]["localizations"]["fr-FR"]`.
   - SSE-emit `agent_complete` with the bundled object and `run_id`.

All five steps reuse existing infrastructure. No changes to `client.py`, no new event loop, no new logging library.
