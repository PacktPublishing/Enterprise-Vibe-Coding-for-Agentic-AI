# Chapter 7 — Loop Engineering

Companion assets for **Chapter 7: Loop Engineering** from *From Vibe Coding to Enterprise Agentic Development*.

Loop engineering is the discipline of not prompting an agent, but designing the **loop that
prompts the agent** — a recurring, verifiable workflow that carries context from a filed issue
to a governed merge, then repeats. You show up at exactly two gates: **approve the plan** and
**authorize the merge**.

➡️ **[Launch the Chapter 7 interactive experience](https://valentina-alto.github.io/Enterprise-Vibe-Coding-for-Agentic-AI/chapter7/chapter7-landing.html)** — a gamified, two-tab tour of the loop and its primitives.

## The loop — five capabilities

Every iteration passes through the same five recurring capabilities, all steered from GitHub
Copilot CLI with `/loop`:

| Capability | What it does | Steered by |
|---|---|---|
| **1. Discover** | Read the issue, load conventions, turn a fuzzy request into an executable objective. Nothing is built yet | `deliver-feature.loop.md` · `copilot-instructions.md` · `SKILL.md` · `feature-loop.yml` |
| **2. Plan** *(gate)* | Produce a reviewable plan, then **stop** for approval — you review thinking, not typing | `SKILL.md` |
| **3. Execute** | Once approved, work autonomously in small, intent-named slices | `deliver-feature.loop.md` · `pre-pr.json` |
| **4. Verify & Recover** | Self-validate each iteration; a red check becomes the next input, not an interruption | `verify.yml` · `.vscode/mcp.json` |
| **5. Complete** *(gate)* | Every acceptance box checked + CI green → prepare the PR and stop. You merge | `verify.yml` (done-condition) |

**None of these artifacts mention the feature being built.** They are issue-agnostic — build
the loop once, and every future issue rides the same rails.

## The six primitives

| Primitive | File | Job |
|---|---|---|
| The engine | `.github/prompts/deliver-feature.loop.md` | What `/loop` runs — one tick, one capability |
| The protocol | `.github/skills/deliver-feature/SKILL.md` | Single source of truth for the five capabilities + two gates |
| The conventions | `.github/copilot-instructions.md` | Always-on law, auto-loaded every turn |
| The contract | `.github/ISSUE_TEMPLATE/feature-loop.yml` | Machine-checkable acceptance checklist |
| The verifier | `.github/workflows/verify.yml` | **Verify & Recover** on every push + gates **Complete** |
| The guardrails | `.github/hooks/pre-pr.json` + `.vscode/mcp.json` | Keep **Execute** off `main`; least-privilege connector |

## Start the loop

Type one command in GitHub Copilot CLI. `/loop` schedules the engine prompt to re-run on an
interval *for the session*; each tick advances the loop by one capability, then stops — so the
two human gates always hold.

```text
/loop 15m advance the delivery loop for issue #1 by one capability using @.github/prompts/deliver-feature.loop.md
```

Everything durable lives in the **issue and PR thread** — the loop's only memory. Close the
terminal and the loop stops.

▶️ **Run it end-to-end** in the companion test repo: **[loop-engineering-test](https://github.com/Valentina-Alto/loop-engineering-test)**.

## Try the guardrail hook

```bash
echo '{"tool_input":{"command":"git push origin main"}}' | python .github/hooks/scripts/pre_pr_check.py
# → BLOCKED — Direct push to `main` is not allowed. (exit 2)
echo '{"tool_input":{"command":"git push origin feature/4-launch-page"}}' | python .github/hooks/scripts/pre_pr_check.py
# → allowed (exit 0)
```

## Files

- [chapter7-landing.html](chapter7-landing.html) — Interactive landing page
- [.github/copilot-instructions.md](.github/copilot-instructions.md) — Always-on law
- [.github/skills/deliver-feature/SKILL.md](.github/skills/deliver-feature/SKILL.md) — The loop protocol (skill)
- [.github/prompts/deliver-feature.loop.md](.github/prompts/deliver-feature.loop.md) — The engine `/loop` runs
- [.github/ISSUE_TEMPLATE/feature-loop.yml](.github/ISSUE_TEMPLATE/feature-loop.yml) — Loop-ready issue form (contract)
- [.github/workflows/verify.yml](.github/workflows/verify.yml) — Verify & Recover + Complete done-condition
- [.github/hooks/pre-pr.json](.github/hooks/pre-pr.json) — Execute guardrail
- [.vscode/mcp.json](.vscode/mcp.json) — Least-privilege GitHub MCP connector
