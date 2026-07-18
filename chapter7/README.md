# Chapter 7 — Loop Engineering

Companion assets for **Chapter 7: Loop Engineering** from *Agentic Development in Practice*.

Loop engineering is the discipline of closing the gap between having good primitives and
having a *system*. Instead of prompting an agent, you design the **loop that prompts the
agent** — a recurring, verifiable workflow that carries context from a filed issue all the way
to a governed merge, and then repeats. Primitives are the vocabulary, RPI is the grammar,
governance is the law, and the loop is the running program.

## 🎮 Interactive Chapter Experience

A two-tab gamified landing page:

1. **The Loop** — Prompt-centric vs system-centric, the anatomy of a delivery loop
   (clickable stages), the worked example as an end-to-end timeline, guardrails,
   anti-patterns, and a knowledge check.
2. **Loop Primitives** — An interactive repository tree of the committed loop artifacts,
   with excerpts for each file.

➡️ **[Launch the Chapter 7 Interactive Experience](https://valentinaalto.github.io/agentic-development-in-practice/code-and-assets/chapter7/chapter7-landing.html)**

## The delivery loop — five capabilities

Instead of a long list of phases, hold the loop in your head as **five recurring
capabilities**. Every iteration passes through them, and the whole loop is steered from
GitHub Copilot CLI with `/loop`.

| Capability | What it does | Steered by |
|---|---|---|
| **1. Discover** | Read the issue, load repo conventions, turn a fuzzy request into an executable objective. Ambiguity disappears; nothing is built yet | `deliver-feature.loop.md`, `AGENTS.md`, `deliver-feature/SKILL.md`, `feature-loop.yml` |
| **2. Plan** *(gate)* | Produce a reviewable plan (files, strategy, tests, assumptions), then **stop** for approval — you review thinking, not typing | `deliver-feature/SKILL.md` |
| **3. Execute** | Once approved, the loop autonomously works in small, intent-named slices | `deliver-feature.loop.md` (one slice/tick), `pre-pr.json` |
| **4. Verify & Recover** | Every iteration self-validates; a red check becomes the next iteration's input, not an interruption | `verify.yml`, `.vscode/mcp.json` |
| **5. Complete** *(gate)* | Every acceptance box checked + CI green → prepare the PR and stop. You merge. "PR opened" is not "done" | `verify.yml` (done-condition) |

The crucial property: **none of these artifacts mention the feature being built.** They are
issue-agnostic — you build the loop once, and every future issue rides the same rails.

## How to start the loop

The loop is driven from **GitHub Copilot CLI**. You type `/loop`, which schedules the engine
prompt to re-run on an interval *for the session*; each tick advances the loop by exactly one
capability and then stops, so the two human gates are always respected:

```text
/loop 15m advance the delivery loop for issue #1 by one capability using @.github/prompts/deliver-feature.loop.md
```

Everything durable lives in the **issue and PR thread** — the loop's only memory. Close the
terminal and the loop stops; that is the point of a session-scoped, human-steered loop.

*Loop engineering* is the discipline of encoding that typed `/loop` as versioned, reviewable
infrastructure — a skill, a prompt, conventions, a contract, a verifier, and guardrails — so
the loop enforces the same protocol on every issue instead of living in your head.

## Loop primitives in this chapter

Six primitives, each with one job:

| Primitive | File | Capability it steers |
|---|---|---|
| The engine | `.github/prompts/deliver-feature.loop.md` | What `/loop` runs — one tick, one capability |
| The protocol | `.github/skills/deliver-feature/SKILL.md` | Single source of truth for the five capabilities + two gates |
| The conventions | `AGENTS.md` | Always-on repo facts loaded during **Discover** |
| The contract | `.github/ISSUE_TEMPLATE/feature-loop.yml` | Machine-checkable acceptance checklist |
| The verifier | `.github/workflows/verify.yml` | **Verify & Recover** on every push + gates **Complete** |
| The guardrails | `.github/hooks/pre-pr.json` + `.vscode/mcp.json` | Keep **Execute** off `main`; least-privilege connector |

## Try the guardrail hook

The `pre-pr` hook is a fast, fail-safe guard that blocks direct pushes to `main` and any
attempt to bypass required checks:

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | python .github/hooks/scripts/pre_pr_check.py
# → pre-pr guard: BLOCKED — Direct push to `main` is not allowed. (exit 2)

echo '{"tool_input":{"command":"git push origin feature/4-launch-page"}}' | python .github/hooks/scripts/pre_pr_check.py
# → allowed (exit 0)
```

## Files

- [chapter7-landing.html](chapter7-landing.html) — Interactive landing page
- [worked-example.md](worked-example.md) — The worked example as a real, reproducible run (companion test repo)
- [AGENTS.md](AGENTS.md) — Repository conventions loaded during Discover
- [.github/skills/deliver-feature/SKILL.md](.github/skills/deliver-feature/SKILL.md) — The loop protocol as a skill (single source of truth)
- [.github/prompts/deliver-feature.loop.md](.github/prompts/deliver-feature.loop.md) — The engine `/loop` runs (schedulable prompt)
- [.github/ISSUE_TEMPLATE/feature-loop.yml](.github/ISSUE_TEMPLATE/feature-loop.yml) — Loop-ready issue form (the contract)
- [.github/workflows/verify.yml](.github/workflows/verify.yml) — Verify & Recover + the Complete done-condition
- [.github/hooks/pre-pr.json](.github/hooks/pre-pr.json) — Execute guardrail
- [.vscode/mcp.json](.vscode/mcp.json) — Least-privilege GitHub MCP connector
