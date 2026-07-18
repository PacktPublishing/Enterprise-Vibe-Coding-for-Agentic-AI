---
name: deliver-feature
description: >
  The team-standard "how we ship" capability. Run any well-formed feature issue
  through the delivery loop's five recurring capabilities — Discover, Plan,
  Execute, Verify & Recover, Complete — with a human gate before Execute (approve
  the plan) and after Complete (authorize the merge). This skill IS the protocol:
  it is the policy source the `/loop` prompt invokes on every tick. Issue-agnostic
  on purpose — you build the loop once and every future issue rides the same rails.
---

# Skill: Deliver a Feature Through the Loop

This skill is the reusable protocol the loop runs. It mentions no specific feature on
purpose: you build the loop once, and every future issue rides the same rails.

You do not prompt the agent. You design the loop that prompts the agent — a recurring,
verifiable workflow that carries context from an issue all the way to a governed merge,
and then repeats for the next issue.

## When to use

Use this whenever a feature issue labeled `loop` needs to be delivered. Assume the issue
was filed with the `feature-loop.yml` template, so it arrives loop-ready with a goal,
requirements, and a machine-checkable acceptance checklist.

## How it is driven

The loop is driven from **GitHub Copilot CLI** with the `/loop` command, which schedules
`.github/prompts/deliver-feature.loop.md` to re-run on an interval **for the session**.
Each tick advances the loop by **exactly one capability**, then stops — so the two human
gates are always respected. Close the terminal and the loop stops; that is the point of a
session-scoped, human-steered loop.

Everything durable lives in the **issue and PR thread**. That thread is the loop's only
memory: on every tick, reconstruct where you are from the thread — never from assumptions.

## The five capabilities

Every iteration of the loop passes through these. Read `AGENTS.md` first — it carries the
repository conventions every capability must respect.

### 1. Discover

Turn an informal request into an executable objective.

1. Identify the target loop issue (the number the prompt was invoked with, or the open
   issue labeled `loop`). Read the issue **and** any open PR that references it through the
   GitHub MCP connector.
2. Load `AGENTS.md` (repo conventions) and this skill.
3. Restate the request as **goals**, **constraints**, and the **acceptance checklist
   rephrased as checkable tests**.
4. Make every **assumption** explicit, and raise **open questions** that would change
   behavior. Post all of this back to the thread.

Ambiguity disappears here. Nothing has been implemented yet.

### 2. Plan — **human gate 1**

Produce a reviewable delivery plan:

- A **file-level change map** (each file + its responsibility).
- The **implementation strategy** and a **criterion → test mapping**.
- The **verification approach** and a **rollback note**.
- The **assumptions** the plan rests on.

Then **stop and wait.** Do not write code until a human replies `plan approved`. The
engineer reviews *thinking, not typing* — correcting direction here costs a sentence.
If the feature touches auth, payments, PII, or production, call out the extra hard gate here.

### 3. Execute

After approval, the loop becomes autonomous. Work `feature/<issue>-<slug>` as a sequence of
**small** slices — each tick does one:

- One slice = one coherent, reviewable diff mapped to one plan step.
- Each slice edits files, commits with an intent-stating message, and updates the thread
  with what changed and why.
- Never push to `main`; the `pre-pr` hook enforces this.

The human is no longer driving the implementation. The loop is.

### 4. Verify & Recover

Every iteration validates itself: `verify.yml` runs lint, unit, integration, contract, and
accessibility checks plus repository policy. If verification fails, nothing special happens —
the next tick simply feeds the failure back to the agent, which reads the CI log through the
GitHub MCP connector, patches, and re-verifies. Recovery is part of the loop; the engineer
never copies an error into a prompt by hand.

Pin any ranking/ordering or layout surface with a fixture-locked test so "correct" is a wall
the loop cannot climb over, not a hope.

### 5. Complete — **human gate 2**

The loop closes only when **every** acceptance box is checked with evidence **and** CI is
green — `verify.yml`'s done-condition job refuses to pass otherwise. When the done-condition
is met, prepare the PR, summarize the implementation, collect the evidence, announce readiness,
and **stop.** The final decision — **merge** — belongs to the engineer. "PR opened" is not
"done."

## Decision flow (which capability to run this tick)

1. No understanding comment on the thread yet? → **Discover**.
2. Understanding posted, no plan yet? → **Plan**, then wait.
3. Plan posted but not yet `plan approved`? → **stop** (human gate 1). Re-check next tick.
4. Plan approved, work remaining? → next **Execute** slice, then **Verify & Recover**.
5. A check is red or a review comment arrived? → **Verify & Recover** (patch + re-verify).
6. All acceptance boxes checked + CI green? → **Complete**: announce the merge gate and stop.

## Non-negotiable bounds

- Advance **exactly one** capability per tick, then stop and write state back to the thread.
- Never cross a human gate autonomously: stop before Executing without `plan approved`, and
  stop before merging.
- Sensitive areas (auth, payments, PII, production) add a hard gate regardless of CI — halt
  and ask.
- Treat the MCP connector as least-privilege: read CI logs and write the thread — never hold
  write access to secrets or production.
- This skill is idempotent per tick: if the current capability is already satisfied, do
  nothing and wait for the next tick.
