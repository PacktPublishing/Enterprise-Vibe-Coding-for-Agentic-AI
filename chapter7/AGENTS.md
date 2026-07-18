# AGENTS.md — Repository conventions for the delivery loop

These are the always-on conventions every agent working in this repo must respect. They are
deliberately short: the **delivery protocol** itself lives in the `deliver-feature` skill
(`.github/skills/deliver-feature/SKILL.md`), which is the single source of truth for how a
feature is shipped. This file carries only the repo-specific facts the loop needs during the
**Discover** capability.

## The one idea

> You do not prompt the agent. You design the loop that prompts the agent — a recurring,
> verifiable workflow that carries context from a filed issue to a governed merge, then repeats.

The loop runs as five recurring capabilities — **Discover → Plan → Execute → Verify & Recover
→ Complete** — with exactly two human gates: **approve the plan** and **authorize the merge**.
Everything between runs unattended. See the `deliver-feature` skill for the full protocol.

## How work is delivered here

- Every feature starts as an issue filed from the **🔁 Feature Loop** template
  (`.github/ISSUE_TEMPLATE/feature-loop.yml`) and labeled `loop`.
- It is driven from GitHub Copilot CLI: `/loop` schedules
  `.github/prompts/deliver-feature.loop.md`, which invokes the skill one capability per tick.
- The **issue/PR thread is the only memory.** Write every assumption, decision, and status
  back to it. When a human answers an open question, that answer is durable state for every
  later capability.

## Conventions

- **Branches:** work on `feature/<issue-number>-<slug>`. Never push directly to `main`; never
  bypass required checks. The `pre-pr` hook (`.github/hooks/pre-pr.json`) enforces this.
- **Commits:** one slice = one small, reviewable diff mapped to one plan step; the commit
  message states intent.
- **Verification is a stage, not an afterthought.** Every acceptance criterion maps to a
  concrete, machine-checkable signal. Any ranking, ordering, or layout surface is pinned by a
  fixture-locked test. `verify.yml` runs on every push.
- **Done-condition is a hard gate.** "PR opened" is not "done." The PR body carries the
  acceptance checklist; the done-condition job refuses to pass while any `- [ ]` is unchecked.
  Do not mark a box without evidence.
- **Sensitive areas add a hard gate regardless of CI:** authentication/authorization,
  payments/billing, PII/regulated data, and production actions (deploys, migrations, secret
  access). Never trade an explicit gate here for speed.
- **Least privilege.** Treat MCP connectors like production dependencies: read CI logs and
  write to the thread — never hold write access to secrets or production. Hooks stay fast
  (< a few seconds) and fail safe.
