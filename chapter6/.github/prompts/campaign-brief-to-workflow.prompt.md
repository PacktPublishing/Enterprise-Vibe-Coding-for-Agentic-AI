---
description: "Scaffold the full set of CMO marketing-campaign app components from a campaign brief: pipeline agents, channel adapters, approval gates, localization, data models, audit/event flow, and SSE wiring. Developer-facing scaffolder, NOT a runtime campaign generator."
name: "Campaign Brief → App Workflow"
argument-hint: "campaign brief: goal, channels, locales, approval rules (e.g. 'Q4 GenZ sneaker launch; channels: instagram, tiktok, reddit; locales: en-US, fr-FR; CMO approval before publish')"
agent: "agent"
---

# Campaign Brief → App Workflow

You are scaffolding **developer-facing app components** inside `cmo-marketing-campaign/` to support a new marketing campaign brief. The runtime pipeline (Strategy → Content → Visual → Audience → Performance + channel adapters) already exists. Your job is to **extend it** with whatever this brief needs, using the team's conventions — not to invent a new architecture and not to *run* the campaign.

This is **NOT** the same as the runtime prompts the product sends to its agents. Those prompts ask agents to *produce* a campaign. This prompt asks **you (the coding agent)** to *produce code* that the product will then run.

## Required reading before you write any code

1. Skill [`marketing-workflow-agents`](../skills/marketing-workflow-agents/SKILL.md) — house conventions, the §1–§5 scaffolds for pipeline / channel / localization / approval / audit, the quality checklist, and the anti-patterns. Every file you generate must conform.
2. Skill [`maf-orchestration-patterns`](../skills/maf-orchestration-patterns/SKILL.md) — only consult if the brief asks for a shape other than Sequential (e.g. concurrent A/B variants, group-chat reviewer loop, magentic open-ended research).
3. Existing references:
   - [cmo-marketing-campaign/agents/__init__.py](../../cmo-marketing-campaign/agents/__init__.py) — registry shape.
   - [cmo-marketing-campaign/agents/email_channel.py](../../cmo-marketing-campaign/agents/email_channel.py) and [linkedin_channel.py](../../cmo-marketing-campaign/agents/linkedin_channel.py) — canonical channel-adapter style.
   - [cmo-marketing-campaign/app.py](../../cmo-marketing-campaign/app.py) — the SSE generator and per-stage event shapes.

If any of these are not yet in context, read them before drafting.

## Inputs (ask only if the brief is silent)

The brief should give you most of these. Ask for the missing ones in a **single grouped question**.

| Input | Default if unspecified |
|---|---|
| `campaign_id` (snake_case) | derive from goal — e.g. `q4_genz_sneakers` |
| `new_pipeline_stages` (list of `{name, role, upstream_inputs}`) | empty |
| `channels` (subset of `email, instagram, tiktok, linkedin` + new ones) | reuse existing four |
| `locales` (IETF tags) | `en-US` only (no localization layer added) |
| `approval_mode` per stage | none for existing, `agent_review` for any new auto-generated stage, `human_gate` only if brief mentions sign-off |
| `audit_required` | true if `human_gate` is anywhere, else false |
| `data_models` (any new structured types the brief needs) | none |
| `event_flow` changes (new SSE events, new endpoints) | minimal additions only |

Do **not** ask about: Flask plumbing, async loop, image generation, JSON parsing — these are fixed by the existing infrastructure.

## Hard constraints (do not negotiate)

- All new agents follow the two-symbol contract: module exports `INSTRUCTIONS: str` and `create_agent(client, tools=None) -> Agent`. (See §1 of the skill.)
- All agents return **strict JSON** matching a literal schema in the prompt. Pipeline code calls `parse_agent_json(raw, "<name>")`.
- Channel adapters are **pure transforms of `results`** — they MUST NOT call upstream agents.
- Localization wraps a channel output; it preserves the JSON shape and lives under `results["<channel>"]["localizations"]["<locale>"]`. Never overwrite the source-language output.
- Approvals never block the SSE generator with `sleep`/`input()`. Use the pause-and-resume pattern from §4b (emit `approval_required`, return; resume endpoint replays from stored `results`).
- Every agent run goes through the shared `_loop` via `asyncio.run_coroutine_threadsafe(...)`. No `asyncio.run()` in request handlers, no new event loops.
- If `audit_required`, wrap every agent call with `run_audited(agent, prompt, stage=..., run_id=run_id)` from §5 and stamp `run_id` on every SSE event.
- Do **not** modify `cmo-marketing-campaign/agents/client.py` unless the brief introduces a new model deployment or a new shared helper. Document the reason in the change summary if you do.
- Do **not** touch `templates/index.html` to display new fields unless the user explicitly asks; the front-end is out of scope.

## What to produce

Return your work as a **single change set** in this order. Use the patterns in `marketing-workflow-agents/SKILL.md` (§1–§5) — do not re-derive them.

### 1. Brief restatement

A 4–6 line bullet list of what you parsed: `campaign_id`, channels (existing/new), locales, approval mode, audit on/off, new pipeline stages. Surface any ambiguity here, before writing code.

### 2. Component plan (table)

| Component | Type | New / Reuse | File |
|---|---|---|---|
| `<name>` | pipeline agent / channel / localizer / reviewer / audit / endpoint | New / Reuse | `cmo-marketing-campaign/agents/<file>.py` |

Mark obvious things as `Reuse` so the user can see you didn't duplicate.

### 3. Data models

If the brief introduces structured fields the existing pipeline doesn't carry (e.g. `loyalty_tier`, `compliance_disclaimer`, `experiment_arm`), declare them once as a typed dict / dataclass in `cmo-marketing-campaign/agents/models.py` (create the file if it does not exist) and reference the same shape from every agent's JSON schema. Do not let two agents disagree on a field.

### 4. Agent modules

For each new agent, produce the full file content following the templates in:

- §1 — pipeline agent
- §2 — channel adapter (mirror `email_channel.py` exactly — same docstring style, INSTRUCTIONS prose, JSON schema block, `create_agent` factory)
- §3 — localizer
- §4a — brand / legal reviewer

Each file is a single ```python``` code block prefixed by the absolute target path. JSON schemas in INSTRUCTIONS must list every field the downstream code will read.

### 5. Registry edit

Show the **exact unified diff** for `cmo-marketing-campaign/agents/__init__.py`:

- module import
- `<name>_agent = <module>.create_agent(client)` line
- entry added to `MAIN_AGENTS` / `CHANNEL_AGENTS` / (new) `REVIEWER_AGENTS`
- `IMAGE_CHANNELS` update if the new channel needs an image

### 6. Pipeline / endpoint wiring (app.py)

Use one of these shapes — pick by brief:

- **New pipeline stage** → numbered section pasted into `generate()` at the correct position, using the §1 SSE pattern (`agent_start` / `log` / `agent_complete` / `agent_error`). Show the diff with surrounding context.
- **New channel endpoint** → new `POST /channels/<channel>` route that:
  - reads `results` from the request body (no upstream re-run),
  - schedules the channel agent on `_loop`,
  - emits SSE if streamed or returns JSON if single-shot,
  - loops localizers per requested locale,
  - applies brand-review per §4a if configured.
- **Human approval gate** → SSE `approval_required` emit + `POST /approve/<approval_id>` + `POST /generate/resume/<approval_id>`, with in-memory `app.config["pending_approvals"]` keyed by uuid. Persist `results` + `run_id` + current stage so resume picks up correctly.

### 7. Event flow (SSE contract)

Enumerate **every** SSE event type the new code emits, with payload schema. Include `run_id` on every event if audit is on. Mark which are new vs already in the contract. Do not introduce two events for the same thing — extend, don't fork.

Example:

```
agent_start         { type, agent, time, run_id }                        # existing, +run_id
approval_required   { type, stage, approval_id, data, time, run_id }     # NEW
approval_resolved   { type, approval_id, decision, feedback, time }      # NEW
```

### 8. Audit + run id (only if `audit_required`)

Show the `audit.py` import in `app.py`, the `run_id = uuid.uuid4().hex` at the top of `generate()`, and one example of replacing a direct `agent.run` with `run_audited(...)`. Don't paste the whole file — diff only.

### 9. Quality checklist (must check every box)

Reproduce the checklist from `marketing-workflow-agents/SKILL.md` §Quality and tick each item against what you generated. If any is unchecked, fix the code, don't ship the gap.

### 10. Run instructions

A 3-line block showing how the developer exercises the new flow locally:

```powershell
cd cmo-marketing-campaign
python app.py
# then open http://127.0.0.1:5000 and submit a brief matching <campaign_id>
```

If you added a new endpoint, include a `curl.exe` example with a representative JSON body.

## What NOT to do

- Don't write runtime *campaign* prompts (headlines, taglines, hero images). That's the agents' job at runtime. You write the agent's INSTRUCTIONS, not its outputs.
- Don't build a "meta-agent" that calls strategy + content + channel itself. Use the existing pipeline.
- Don't add a new dependency to `requirements.txt` unless the brief truly forces it. Justify in the change summary if you do.
- Don't change `client.py`'s deployment names, endpoint, or token provider.
- Don't introduce a database. Audit goes to JSONL on disk per §5; pending approvals stay in `app.config`.
- Don't generate front-end code. The brief is about the agent/workflow layer.

## Closing summary (always end with this)

After the change set, write:

1. **Pipeline diagram** — 4–8 line ASCII showing the stages in order, with approval gates and localization branches marked.
2. **Files touched** — bulleted list with status (new / modified) and 1-line purpose each.
3. **Suggested follow-ups** — at most 3 items the developer should consider next (e.g. "add a `PreToolUse` hook to enforce the two-symbol contract", "write a runtime brief example for `<campaign_id>` to seed the form", "add a unit test for the new channel's JSON schema").
