# Chapter 7 — Loop Engineering

Companion assets for **Chapter 7: Loop Engineering** from *Agentic Development in Practice*.

Loop engineering is the discipline of closing the gap between having good primitives and
having a *system*. Instead of prompting an agent, you design the **loop that prompts the
agent** — a recurring, verifiable workflow that carries context from a trigger all the way
to a governed merge, and then repeats. Primitives are the vocabulary, RPI is the grammar,
governance is the law, and the loop is the running program.

## 🎮 Interactive Chapter Experience

A two-tab gamified landing page:

1. **The Loop** — Prompt-centric vs system-centric, the P0–P8 anatomy of a delivery loop
   (clickable stages), the airline trip-planner worked example as an end-to-end timeline,
   guardrails, anti-patterns, and a knowledge check.
2. **Loop Primitives** — An interactive repository tree of the committed `.github` loop
   artifacts, filterable by loop stage, with excerpts for each file.

➡️ **[Launch the Chapter 7 Interactive Experience](https://valentinaalto.github.io/agentic-development-in-practice/code-and-assets/chapter7/chapter7-landing.html)**

## The delivery loop (P0–P8)

| Stage | What it does | Implemented by |
|-------|--------------|----------------|
| **P0** Trigger | Turns a workflow from *something you run* into *something that runs* | `loop-dispatch.yml` (cron + `issues: assigned`) |
| **P1** Normalize intent | Fuzzy request → checkable contract (goals, constraints, acceptance, assumptions) | `copilot-instructions.md`, `deliver-feature/SKILL.md`, `feature-loop.yml` |
| **P2** Plan (gate) | Reviewable spec, then stop for approval | Agent plan mode + approval |
| **P3** Implement in slices | Small, coherent commits, one per plan step | Autopilot / Fleet |
| **P4** Verify | lint · unit · integration · contract + deterministic fixture | `loop-verify.yml` |
| **P5** Auto-recover | A red check / review comment is the next input, not an interruption | Coding agent + GitHub MCP |
| **P6** Human gates | Exactly two: approve the plan, authorize the merge | Approvals + branch protection + `pre-pr.json` |
| **P7** Persist memory | The issue / PR thread *is* the database | Thread via GitHub MCP |
| **P8** Done-condition | "PR opened" is not "done" — every box checked + CI green | `loop-verify.yml`, `pre-pr.json` |

The crucial property: **none of these artifacts mention the feature being built.** They are
issue-agnostic — you build the loop once, and every future issue rides the same rails.

## Loop primitives in this chapter

| Type | File | Loop stage |
|------|------|------------|
| Instructions | `.github/copilot-instructions.md` | P1 / P6 (always-on rulebook) |
| Skill | `.github/skills/deliver-feature/SKILL.md` | P1 ("how we ship") |
| Issue template | `.github/ISSUE_TEMPLATE/feature-loop.yml` | P1 (structured trigger input) |
| Workflow | `.github/workflows/loop-dispatch.yml` | P0 (trigger, throttled + idempotent) |
| Workflow | `.github/workflows/loop-verify.yml` | P4 + P8 (verify + done-condition) |
| Hook | `.github/hooks/pre-pr.json` + `scripts/pre_pr_check.py` | P6 / bounds (guardrail) |
| MCP | `.vscode/mcp.json` | P5 / P7 (least-privilege connector) |

## Try the guardrail hook

The `pre-pr` hook is a fast, fail-safe guard that blocks direct pushes to `main` and any
attempt to bypass required checks:

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | python .github/hooks/scripts/pre_pr_check.py
# → pre-pr guard: BLOCKED — Direct push to `main` is not allowed. (exit 2)

echo '{"tool_input":{"command":"git push origin feature/2194-trip-planner"}}' | python .github/hooks/scripts/pre_pr_check.py
# → allowed (exit 0)
```

## Files

- [chapter7-landing.html](chapter7-landing.html) — Interactive landing page
- [.github/copilot-instructions.md](.github/copilot-instructions.md) — Always-on rulebook
- [.github/skills/deliver-feature/SKILL.md](.github/skills/deliver-feature/SKILL.md) — The loop protocol as a skill
- [.github/ISSUE_TEMPLATE/feature-loop.yml](.github/ISSUE_TEMPLATE/feature-loop.yml) — Loop-ready issue form
- [.github/workflows/loop-dispatch.yml](.github/workflows/loop-dispatch.yml) — P0 trigger
- [.github/workflows/loop-verify.yml](.github/workflows/loop-verify.yml) — P4 verify + P8 done-condition
- [.github/hooks/pre-pr.json](.github/hooks/pre-pr.json) — P6 / bounds guardrail
- [.vscode/mcp.json](.vscode/mcp.json) — Least-privilege GitHub MCP connector
