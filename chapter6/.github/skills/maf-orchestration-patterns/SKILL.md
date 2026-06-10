---
name: maf-orchestration-patterns
description: 'Pick and scaffold the right Microsoft Agent Framework (MAF) orchestration pattern — sequential, concurrent, group chat, magentic, or handoff — for a multi-agent project. USE FOR: choosing an orchestration pattern, scaffolding a MAF workflow, designing multi-agent systems with agent_framework, deciding between sequential/concurrent/handoff/group-chat/magentic, building a travel agent, customer support router, content pipeline, research assistant, brainstorming ensemble, writer-reviewer loop, or any new multi-agent product on MAF. Reads at the start of any multi-agent project. DO NOT USE FOR: single-agent apps, non-MAF frameworks (Semantic Kernel core, AutoGen, LangGraph), deploying agents to Foundry (use microsoft-foundry skill), or general agent code review.'
---

# MAF Orchestration Patterns

A procedural guide to the five built-in Microsoft Agent Framework (MAF) orchestration patterns. Use this at the **start of any new multi-agent project** to choose the right pattern, then follow the matching scaffold to stand up a minimal working workflow.

Source of truth: [Workflow orchestrations — Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/).

## The five patterns at a glance

| Pattern | Topology | Control | Use when… |
|---|---|---|---|
| **Sequential** | Pipeline | Static order | Each step strictly depends on the previous one (review → edit → publish). |
| **Concurrent** | Fan-out / fan-in | Parallel, independent | Same input, multiple perspectives (ensemble, voting, brainstorming). |
| **Group Chat** | Star (manager + participants) | Manager picks next speaker (round-robin / custom) | Iterative refinement among peers (writer ↔ reviewer until "approved"). |
| **Magentic** | Star with **planning** manager | Manager plans, replans on stall | Open-ended tasks where the path is **not known in advance** (research + code + synthesis). |
| **Handoff** | Mesh (no orchestrator) | Agents transfer ownership | Dynamic routing by domain expertise (triage → flight / hotel / support). |

## Step 1 — Pick the pattern

Walk this decision flow **in order**. Stop at the first match.

1. **Is the path fixed and linear?** → **Sequential**
   *Example: assess → plan → execute; translate → summarize → tag.*

2. **Do agents work on the same input independently and you combine their outputs?** → **Concurrent**
   *Example: three reviewers score a paper; N translators produce variants.*

3. **Does a user (or upstream router) hand off ownership to one specialist that fully owns the rest of the turn, with possible bounce-back to a triage agent?** → **Handoff**
   *Example: travel concierge → flight specialist; support triage → billing / refunds / tech.*
   - Use handoff over Group Chat when **only one agent should respond at a time** and **the receiving agent takes full ownership** (not just contributes a turn).
   - Use handoff over agent-as-tools when the **receiving agent owns the conversation**, not just a subtask.

4. **Do multiple agents need to converse, refining each other's work until a termination condition?** → **Group Chat**
   *Example: copywriter ↔ reviewer loop until reviewer approves; debate panel.*

5. **Is the task open-ended, requires a plan, and the plan may need to change mid-flight?** → **Magentic**
   *Example: "research X, run analysis, produce a report" — manager plans, picks the next specialist each round, detects stalls, replans.*

### Disambiguation cheatsheet

- **Group Chat vs Magentic**: Group Chat coordinates *who speaks*; Magentic also *plans and replans*. Default to Group Chat unless you need dynamic planning.
- **Handoff vs Group Chat**: Handoff = ownership transfer, no central orchestrator, mesh topology. Group Chat = central manager, all agents see all history.
- **Handoff vs agent-as-tools**: Handoff transfers control and context. Agent-as-tools keeps the primary agent in charge and treats sub-agents as callable tools.
- **Sequential vs Group Chat round-robin**: Sequential runs each agent **once** in fixed order. Round-robin Group Chat can run **N iterations**.

## Step 2 — Scaffold

Each pattern below is a minimal Python scaffold using `agent_framework`. Replace agent instructions and the client setup with your project's specifics, then iterate.

> **Client setup (shared across all scaffolds).** Use whatever client your project already wires up (Azure OpenAI, OpenAI, Foundry Project). The scaffolds assume a `client` and an `Agent` factory like the ones in this repo's `agents/client.py`.

### Sequential — `AgentWorkflowBuilder.build_sequential`

```python
from agent_framework import Agent, AgentWorkflowBuilder, InProcessExecution, ChatMessage, ChatRole, TurnToken

def make_agent(instructions, name):
    return Agent(client, instructions, name=name)

draft = make_agent("Draft a short blog post on the topic.", "Drafter")
edit  = make_agent("Edit the draft for clarity and tone.", "Editor")
seo   = make_agent("Rewrite the title and add 3 SEO tags.", "SEO")

workflow = AgentWorkflowBuilder.build_sequential([draft, edit, seo])

run = await InProcessExecution.run_streaming(workflow, [ChatMessage(ChatRole.USER, "Topic: agentic AI in 2026")])
await run.try_send_message(TurnToken(emit_events=True))
async for evt in run.watch_stream():
    ...  # print per-agent updates; capture WorkflowOutputEvent for final messages
```

**Heuristics**
- Each agent sees previous agent(s)' full conversation by default. Switch to response-only context if upstream history is noisy.
- Add `ApprovalRequiredAIFunction` on sensitive tools to insert a HITL gate.

### Concurrent — `AgentWorkflowBuilder.build_concurrent`

```python
fr = make_agent("Translate to French. Reply only in French.", "fr")
es = make_agent("Translate to Spanish. Reply only in Spanish.", "es")
de = make_agent("Translate to German. Reply only in German.",  "de")

workflow = AgentWorkflowBuilder.build_concurrent([fr, es, de])
# Run identically to sequential; results are aggregated automatically.
```

**Heuristics**
- Use when agents are **stateless w.r.t. each other**. If one needs another's output, you want Sequential or Group Chat.
- Add a final aggregator agent downstream (Sequential of [Concurrent block, Aggregator]) when you need a single synthesized answer.

### Group Chat — `AgentWorkflowBuilder.create_group_chat_builder_with`

```python
from agent_framework import RoundRobinGroupChatManager

writer   = make_agent("You write punchy marketing slogans.", "Writer")
reviewer = make_agent("You critique slogans. Reply 'APPROVED' when satisfied.", "Reviewer")

workflow = (
    AgentWorkflowBuilder
    .create_group_chat_builder_with(lambda agents: RoundRobinGroupChatManager(agents, maximum_iteration_count=6))
    .add_participants(writer, reviewer)
    .build()
)
```

**Heuristics**
- Subclass `RoundRobinGroupChatManager` and override `should_terminate_async` for content-based exits (e.g., reviewer says "approve").
- Cap `maximum_iteration_count` low (4–6) while iterating; raise once stable.

### Magentic — `MagenticWorkflowBuilder`

```python
from agent_framework import MagenticWorkflowBuilder

researcher = make_agent("Find relevant facts. No math.", "Researcher")
coder      = make_agent("Write and execute Python to compute answers.", "Coder")
manager    = make_agent("Coordinate the team to solve the task.", "Manager")

workflow = (
    MagenticWorkflowBuilder(manager)
    .add_participants([researcher, coder])
    .with_max_rounds(10)
    .with_max_stalls(3)
    .with_max_resets(2)
    .require_plan_signoff(False)  # set True to add HITL plan review
    .build()
)
```

**Heuristics**
- Start with `require_plan_signoff=True` during development to inspect the plan; flip to `False` for unattended runs.
- Listen for `MagenticOrchestratorEvent` (PLAN_CREATED / REPLANNED / PROGRESS_LEDGER_UPDATED) in your event loop to surface "thinking" to the UI.

### Handoff — `AgentWorkflowBuilder.create_handoff_builder_with`

```python
triage  = make_agent("Greet customer; route ONLY when they explicitly ask.", "triage")
flight  = make_agent("You handle flight searches and bookings.", "flight")
hotel   = make_agent("You handle hotel searches and bookings.", "hotel")

workflow = (
    AgentWorkflowBuilder
    .create_handoff_builder_with(triage)
    .with_handoffs(triage, [flight, hotel])      # triage can hand off to either
    .with_handoffs([flight, hotel], triage)      # specialists can return to triage
    .build()
)
```

**Heuristics**
- The `HandoffAgentExecutor` injects handoff tools automatically — do **not** add manual "transfer" tools.
- Tell the triage agent in its instructions whether to be **proactive** (route on inference) or **explicit-only** (route only when asked). See this repo's `travel agency/agents/triage_agent.py` for an "explicit-only" pattern.
- Specialists should hand back to triage after completing their work so the conversation has a natural re-entry point.

## Step 3 — Quality checks before you ship

Run through this checklist regardless of pattern:

- [ ] **Pattern justified in code/README** — one sentence saying why this pattern was picked over the runner-up.
- [ ] **Termination is bounded** — `maximum_iteration_count` (Group Chat), `with_max_rounds` / `with_max_stalls` / `with_max_resets` (Magentic), explicit stop conditions (Handoff loop).
- [ ] **Event handling** — UI surfaces per-agent updates via `AgentResponseUpdateEvent` and final result via `WorkflowOutputEvent`.
- [ ] **Sensitive tools wrapped** — anything that writes/deploys/spends money uses `ApprovalRequiredAIFunction`.
- [ ] **No hidden god-agent** — if one agent has 8+ tools and 3+ responsibilities, split it and revisit the pattern choice.
- [ ] **Context strategy is explicit** — for Sequential, decide full-history vs response-only; for Handoff/Group Chat, remember agents do not share session instances (the orchestrator broadcasts).

## When to switch patterns mid-project

You picked one and it's fighting you. Common refactors:

- **Sequential → Group Chat**: you keep needing the editor to ask the writer to redo something.
- **Group Chat → Magentic**: the manager keeps picking the wrong next speaker; you need real planning.
- **Magentic → Sequential**: the task turned out to have a fixed recipe; planning overhead is wasted.
- **Concurrent → Sequential of [Concurrent, Aggregator]**: you need a single answer, not N parallel ones.
- **Handoff → Group Chat**: specialists need to **collaborate** on the same turn, not own it alone.

## Worked example — travel agency (this repo)

The `travel agency/` project picks **Handoff** because:
- A concierge greets and routes by **explicit customer request** (flight vs hotel).
- The chosen specialist **owns** the booking flow end-to-end (not a one-shot tool call).
- Specialists hand back to the concierge for "anything else?" — a natural mesh of two ownership transfers.

The runner-up was Group Chat, rejected because only one agent should speak per turn and there is no iterative critique loop.

## References

- Overview: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/
- Sequential: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/sequential
- Concurrent: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/concurrent
- Group Chat: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/group-chat
- Magentic: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/magentic
- Handoff: https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff
- Human-in-the-loop: https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop
