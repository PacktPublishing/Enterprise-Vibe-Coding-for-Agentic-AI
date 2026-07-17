# Copilot Instructions — The Delivery Loop

These instructions are the always-on rulebook for every agent that runs in this
repository. They encode the delivery loop (P0–P8) as policy, so that any feature —
regardless of what it does — rides the same rails from a filed issue to a governed
merge. Nothing here is tribal knowledge; it is reviewable, versioned, and improvable.

## The loop, in one line

> You do not prompt the agent. You design the loop that prompts the agent —
> a recurring, verifiable workflow that carries context from a trigger all the way
> to a governed outcome, and then repeats.

## Operating cadence: Research → Plan → Implement (RPI)

1. **Normalize intent first (P1 — Research).** Restate the raw issue as goals,
   constraints, and explicit, machine-checkable acceptance criteria. Surface
   assumptions and open questions *before* any code exists. Post this understanding
   back to the issue thread. A fuzzy request must become a checkable contract.

2. **Plan behind a human gate (P2 — Plan).** Produce a reviewable spec: a file-level
   change map, a test strategy, and a rollout/rollback note. Then **stop and wait for
   explicit approval.** This is the single most important governance gate — do not
   begin implementation until a human replies `plan approved`.

3. **Implement in bounded slices (P3).** Execute as a sequence of small, coherent
   commits, each mapped to one plan step. One slice = one reviewable diff. Every commit
   message states intent. Do not produce one giant dump.

## Verification is a stage, not an afterthought (P4)

- After every slice, run lint, unit, integration, and contract checks.
- Every acceptance criterion must map to a concrete, machine-checkable signal.
- Ranking, ordering, or any non-deterministic surface must be pinned by a
  fixture-locked test. "Deterministic" is a wall the loop cannot climb over, not a hope.

## Failure feeds back in (P5 — Auto-recover)

A red CI run or a review comment is **the next input to the loop**, not an interruption.
Diagnose, patch, re-run, and continue — without asking for a re-prompt. Read CI logs
through the GitHub MCP connector; the fix is just another commit in the same loop.

## Human decision gates (P6)

Autonomy is bounded to exactly two moments that matter:

- **Approve the plan (P2).**
- **Authorize the merge (P8).**

Everything between runs unattended. **Sensitive areas always add a hard gate,
regardless of how green CI is:**

- Authentication / authorization
- Payments / billing
- PII or regulated data
- Production actions (deploys, migrations, secret access)

Never trade an explicit gate in these areas for speed.

## Memory lives in the thread (P7)

There is no separate database. The issue and PR thread *are* the loop's memory:
assumptions, decisions, status, unresolved questions. Always write decisions back to
the thread so context survives across steps and across days. When a human answers an
open question (e.g. "grey it out"), treat that answer as durable state for every later
stage.

## The done-condition is a hard gate (P8)

- "PR opened" is **not** "done."
- The loop closes only when *every* acceptance criterion is checked with evidence
  (a link to a passing test) **and** the pipeline is green.
- The PR body carries the acceptance checklist. The done-condition job refuses to pass
  while any `- [ ]` remains unchecked. Do not mark a box without evidence.

## Bounds are non-negotiable

- Respect the autopilot continuation cap. If you hit it, stop and summarize state.
- Never push directly to `main`; never bypass required checks.
- Treat MCP connectors as least-privilege: read CI logs and write to the thread —
  never hold write access to secrets or production.
- Hooks must stay fast (< a few seconds) and fail safe.
