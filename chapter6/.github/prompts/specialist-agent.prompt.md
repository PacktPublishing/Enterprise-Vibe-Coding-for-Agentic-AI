---
description: "Scaffold a new specialist agent for the travel-agency Handoff workflow (e.g. car hire, travel insurance, activities). Generates the agent module, registers it, and wires its handoff peers + turn limit."
name: "Add Travel Specialist Agent"
argument-hint: "specialist name + scope (e.g. 'car_hire — searches and books rental cars')"
agent: "agent"
---

# Add a new specialist to the Travel Agency

You are adding a new specialist agent to the `travel agency/` project. The architecture is fixed: a **MAF Handoff workflow** with a concierge (`triage_agent`) that routes to specialists on explicit customer request, and specialists that hand back to the concierge when done. This is not a redesign — it is filling in a template.

## Inputs (ask the user only if missing)

1. **Agent name** — snake_case, e.g. `car_hire_agent`, `insurance_agent`. Must end with `_agent`.
2. **Scope** — one sentence on what the customer asks this agent to do.
3. **Tools** — list of tool names + a one-line purpose each. Mark any that touch real APIs vs mock data. If the user hasn't decided, propose 2 tools: one `search_*` (returns mock JSON) and one `book_*` (returns a mock confirmation code), matching `hotel_agent.py`.
4. **Handoff peers** — by default, the new specialist only hands back to `triage_agent`. Ask only if the user wants cross-specialist handoffs (e.g. flight → car_hire). Cross-handoffs are discouraged; route via triage instead.
5. **Turn limit** — default `3` (matches `hotel_agent`). Bump to `4` if the specialist calls a real external API.

## Constraints (do not negotiate)

- Use **MAF Handoff** orchestration via `HandoffBuilder` — same as existing `app.py`. Do not introduce Sequential / Group Chat / Magentic.
- The new agent **must hand back to `triage_agent`** after presenting results. Do not let it terminate the conversation.
- Tools are decorated with `@tool` and use `Annotated[..., "description"]` parameters — match the style in [hotel_agent.py](./travel%20agency/agents/hotel_agent.py).
- Mock-data tools return `json.dumps({...}, indent=2)`; booking tools return a human-readable confirmation string with a generated `UUID` short code.
- Do **not** touch `templates/index.html` or `static/` — the UI auto-renders any agent the workflow registers.
- Keep new code under ~80 LOC for the agent module unless the user pushes back.

## What to produce

Make four edits in this exact order. After each, briefly say what you did before moving on.

### 1. Create `travel agency/agents/<name>_agent.py`

Model on [hotel_agent.py](./travel%20agency/agents/hotel_agent.py). The file has exactly:
- Docstring header naming the specialist and one-line scope.
- Imports: `json`, `uuid`, `Annotated`, `from agent_framework import Agent, tool`.
- `INSTRUCTIONS` string that:
  - Names the role ("You are a *X* Specialist").
  - Numbered steps for the tools to call.
  - **Mandates** handoff back to `triage_agent` after presenting results.
  - States: "Do NOT hand off to any other specialist. Only hand off back to triage_agent."
  - Tells the agent to ask for missing inputs rather than guess.
- `@tool` functions (one per declared tool).
- `create_agent(client)` factory returning `Agent(client, INSTRUCTIONS, name="<name>_agent", description="...", tools=[...], require_per_service_call_history_persistence=True)`.

### 2. Register in `travel agency/agents/__init__.py`

Add the import and an instance binding alongside `triage`, `flights`, `hotels`. Use a short plural noun for the variable (e.g. `cars`, `insurance`).

### 3. Wire the handoff in `travel agency/app.py`

In `_create_workflow()`:
- Add the new specialist to `participants=[triage, flights, hotels, <new>]`.
- Extend triage's outbound list: `.add_handoff(triage, [flights, hotels, <new>])`.
- Add the return handoff: `.add_handoff(<new>, [triage])`.
- Add the turn limit entry under `with_autonomous_mode(turn_limits={...})`.

### 4. Update triage routing in `travel agency/agents/triage_agent.py`

Add one line under the routing rules:
```
   - <Service> requests -> hand off to <name>_agent
```
Keep the "explicit request only" rule intact — do not make triage proactive.

## After producing

Print a short summary in this shape:

```
Added specialist: <name>_agent
- Tools: <tool_a>, <tool_b>
- Hands back to: triage_agent
- Turn limit: <N>
Run: cd "travel agency" && python app.py  (UI: http://localhost:5001)
Try: "<one sample customer prompt that should reach the new specialist>"
```

## Anti-patterns to refuse

- Adding cross-specialist handoffs "just in case" — refuse unless the user gives a concrete user journey requiring it.
- Adding real third-party API calls without an env-var guard and a mock fallback (mirror `flight_agent.py`'s `AVIATIONSTACK_API_KEY` pattern).
- Letting the specialist end the conversation instead of handing back to triage.
- Renaming or restructuring `app.py` orchestration — the architecture is locked.
