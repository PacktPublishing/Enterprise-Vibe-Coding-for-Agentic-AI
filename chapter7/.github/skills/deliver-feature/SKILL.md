---
name: deliver-feature
description: >
  The team-standard "how we ship" capability. Run any well-formed feature issue
  through the eight-stage delivery loop (P0–P8): normalize intent, plan behind a
  human gate, implement in bounded slices, verify continuously, auto-recover from
  failures, honor the human gates, persist memory in the thread, and enforce the
  done-condition. Issue-agnostic — the same skill ships every feature.
---

# Skill: Deliver a Feature Through the Loop

This skill is the reusable protocol the loop runs. It mentions no specific feature on
purpose: you build the loop once, and every future issue rides the same rails.

## When to use

Use this whenever the loop dispatch assigns you a feature issue labeled `loop`.
Assume the issue was filed with the `feature-loop.yml` template, so it arrives
loop-ready with goals, constraints, and acceptance criteria.

## The protocol

### P1 — Normalize intent (Research)

1. Load `copilot-instructions.md` and this skill.
2. Restate the issue as **goals**, **constraints**, and **acceptance checks**.
3. List every **assumption** explicitly (e.g. "reusing `FaresClient`; ranking weights
   price > duration > stops; budget is a soft filter, not a hard cut-off").
4. Raise **open questions** as a numbered list and stop for answers when a decision
   changes behavior (e.g. "sold-out option: hidden or greyed-out?").
5. Post all of the above back to the issue thread. This is loop memory (P7).

### P2 — Plan behind a human gate (Plan)

Produce a reviewable plan containing:

- A **file-level change map** (each file + its responsibility).
- A **criterion → test mapping**.
- A **rollback note**.

Then **stop.** Do not write code until a human replies `plan approved`.
If the feature touches auth, payments, PII, or production, call out the extra gate here.

### P3 — Implement in bounded slices (Implement)

Work the plan as a sequence of small commits on `feature/<issue>-<slug>`:

- One slice = one coherent, reviewable diff mapped to one plan step.
- Every commit message states intent.
- Independent slices may run in parallel (fleet); dependent slices advance in sequence
  under the continuation cap.

### P4 — Verify continuously (Agentic DevOps)

After each slice, ensure `loop-verify` runs lint, unit, integration, and contract
tests. Keep the criterion mapping live. Pin any ranking/ordering with a fixture-locked
test.

### P5 — Auto-recover

On a red check or a review comment: read the CI log via the GitHub MCP connector,
diagnose, patch, re-run, and continue. The fix is another commit in the same loop —
consistent with earlier decisions still recorded in the thread. Never wait to be pinged.

### P6 — Human decision gates

Only two interventions are expected: **approve the plan** and **authorize the merge**.
Treat review comments as structured loop input, not a restart. Sensitive areas add a
hard gate — respect it unconditionally.

### P7 — Persist memory

Keep the issue and PR thread current: assumptions, decisions, status, unresolved
questions. The thread is the only source of truth.

### P8 — Enforce the done-condition

- Carry the acceptance checklist in the PR body, each box linking to evidence.
- The loop closes only when every `- [ ]` is checked **and** CI is green.
- Never declare "done" early.

## Decision flow

1. Issue just assigned & labeled `loop`? → start at **P1**.
2. Plan not yet approved? → produce/refine plan, **wait** (P2).
3. Plan approved? → implement the next **bounded slice** (P3) + verify (P4).
4. Check red or review comment arrived? → **auto-recover** (P5), loop back to P4.
5. All criteria checked + CI green? → request the **merge gate** (P8).
