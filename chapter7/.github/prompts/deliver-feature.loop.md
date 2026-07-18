---
name: deliver-feature-loop
description: >
  The schedulable prompt that drives the delivery loop from GitHub Copilot CLI.
  Pair it with `/loop` to advance a feature through the loop's five capabilities —
  Discover, Plan, Execute, Verify & Recover, Complete. Each tick advances the loop
  by exactly one capability and then stops, so the two human gates (approve the
  plan, authorize the merge) are always respected.
argument-hint: "The loop issue number, e.g. 1"
---

# Recurring prompt: advance the delivery loop by one capability

This is the engine `/loop` runs. `/loop` schedules this prompt to re-run **for the
session**; each tick performs **one** capability and stops, so closing the terminal stops
the loop. Run it with:

```text
/loop 15m advance the delivery loop for issue #1 by one capability using @.github/prompts/deliver-feature.loop.md
```

## What to do on each tick

1. **Load policy.** Read `.github/copilot-instructions.md` (always-on rules) and run the `deliver-feature`
   skill — that skill is the source of truth for the five capabilities and the two gates.
2. **Reconstruct state.** Identify the target loop issue (the number passed to this prompt,
   or the open issue labeled `loop`). Read the issue **and** any open PR that references it
   through the GitHub MCP connector. The thread is the loop's only memory — determine where
   you are from it, do not assume.
3. **Advance exactly one capability**, following the skill's decision flow:
   - No understanding comment yet → **Discover** (post goals, constraints, assumptions,
     open questions). No code.
   - Understanding posted, no plan yet → **Plan** (post the reviewable plan), then **stop
     and wait** — do not Execute until a human replies `plan approved`. *(Human gate 1.)*
   - Plan not yet approved → **stop**. Re-check next tick.
   - Plan approved, work remaining → do the next **Execute** slice, then ensure
     **Verify & Recover** runs; on a red check or review comment, patch and re-verify.
   - All acceptance boxes checked + CI green → **Complete**: announce the loop is ready for
     the **merge gate** and **stop** — do not merge. *(Human gate 2.)*
4. **Write state back to the thread** so the next tick can pick up exactly where you left off.

## Non-negotiable bounds

- Never push directly to `main`; never bypass required checks (the `pre-pr` hook enforces this).
- Never cross a human gate autonomously: stop before Executing without `plan approved`, and
  stop before merging.
- Sensitive areas (auth, payments, PII, production) add a hard gate regardless of CI — halt
  and ask.
- Idempotent per tick: if the current capability is already satisfied, do nothing and wait
  for the next tick.
