# Worked Example — Watching the Loop Run for Real

Everything in this chapter has been theory with a fictional airline attached. This section
closes that gap: the loop described here is not a diagram — it is a repository you can clone,
trigger, and watch close on itself. Two worlds stay cleanly separated. The **user** is the
customer who will one day type into a chat box and never see GitHub. The **engineering team**
uses loop engineering to build what that user talks to. The chat is the product; the loop is
how the product gets made.

> **Try it yourself.** A companion repository ships every primitive from this chapter, wired
> and live: **<https://github.com/Valentina-Alto/loop-engineering-test>**. Clone it, open an
> issue with the `loop` label, and drive it from your terminal with `/loop`. The walkthrough
> below tracks a real feature — issue #4 in that repo — and the loop comments it quotes are the
> kind the loop posts to the thread at each stage.

## Five capabilities, not eight phases

The clean way to hold the loop in your head is not a list of phases but **five recurring
capabilities**. Every iteration passes through them:

1. **Discover** — the loop reads the issue, loads the repository conventions, and turns an
   informal description into an executable objective. Ambiguity disappears. Nothing is built yet.
2. **Plan** — the loop asks the coding agent for a delivery plan, then pauses. This is the first
   human gate. The engineer reviews *thinking, not typing*, and approves the direction.
3. **Execute** — after approval the loop becomes autonomous, repeatedly invoking the agent in
   small, committed slices until progress is made. The human is no longer driving; the loop is.
4. **Verify & Recover** — every iteration validates itself. If verification fails, nothing
   special happens: the loop feeds the failure back to the agent, asks it to repair, and validates
   again. Recovery is part of the loop.
5. **Complete** — eventually every acceptance criterion is satisfied. The loop prepares the pull
   request, summarises the work, collects the evidence, and stops. The final decision — merge —
   still belongs to the engineer.

## Six primitives that steer it

The capabilities are the *behaviour*; the **primitives** are what make that behaviour happen
without you prompting for it. There are six, and none of them mentions the feature being built —
that is why you build the loop once and every future issue rides the same rails.

| Primitive | File | The capability it steers |
|---|---|---|
| **The engine** | `.github/prompts/deliver-feature.loop.md` | What `/loop` runs. One tick advances **one** capability, then stops at the gates. |
| **The protocol** | `.github/skills/deliver-feature/SKILL.md` | The single source of truth for the five capabilities and the two gates; the engine invokes it every tick. |
| **The conventions** | `AGENTS.md` | Always-on repo facts the loop loads during **Discover**. |
| **The contract** | `.github/ISSUE_TEMPLATE/feature-loop.yml` | Forces a machine-checkable acceptance checklist — the objective **Discover** reads and **Complete** closes on. |
| **The verifier** | `.github/workflows/verify.yml` | Runs on every push (**Verify & Recover**) and gates **Complete**: it refuses to pass while any acceptance box is unchecked. |
| **The guardrails** | `.github/hooks/pre-pr.json`, `.vscode/mcp.json` | Keep **Execute** off `main`; give **Verify & Recover** least-privilege read-CI / write-thread access. |

The loop is driven from **GitHub Copilot CLI**. You type `/loop`, which schedules the engine to
re-run on an interval *for the session*; each tick advances the loop by exactly one capability and
then stops. Everything durable lives in the **issue and PR thread** — the loop's only memory, so
every tick reconstructs where it is from the thread rather than from anything held in your head.

## The run — feature issue #4, the book launch landing page

We file one ordinary issue in the companion repo — *"Create a simple, self-contained HTML landing
page to announce the launch of the book Agentic Development in Practice"* — with four
machine-checkable acceptance boxes, and we drive it from the terminal:

```text
/loop 15m advance the delivery loop for issue #4 by one capability using @.github/prompts/deliver-feature.loop.md
```

Each tick advances the loop by exactly one capability, then stops. Watch it move.

### 1. Discover
The first tick fires. The engine loads `AGENTS.md` and the `deliver-feature` skill, reads the
issue through the GitHub MCP connector, and posts its understanding straight to the thread —
goals, constraints, the acceptance criteria *restated as checkable tests*, and, crucially, its
**assumptions** made explicit:

> *"A single self-contained `index.html` with inline CSS and no build step. Cover is a placeholder
> `<img>` with descriptive `alt` until real art lands. System font stack so nothing loads over the
> network. The 'Get the book' CTA points at a configurable URL, defaulted to a placeholder."*

It raises the questions that would change behavior — *"Do you want a real cover asset now or a
placeholder? Which store URL should the CTA link to? Light theme only, or a dark-mode toggle?"* —
because a fuzzy request has to become a contract *before* code exists. This comment is the loop's
memory: every later capability reads it. Nothing has been built.

### 2. Plan — **GATE 1**
The next tick posts a reviewable plan: a file-level change map (`index.html`, plus a small
`tests/` folder for the checks), a criterion → test mapping, the verification approach, and a
rollback note. Then it **stops.** No file written. You skim the plan and reply **`plan approved`**
in the terminal. This is your **first intervention, and the highest-leverage minute you will spend
on the feature** — you are reviewing *thinking, not typing*. Correcting direction here costs a
sentence; correcting it after a full page is built costs an afternoon.

### 3. Execute
With the plan approved, the loop becomes autonomous. It works `feature/4-launch-page` as small,
intent-named commits — one reviewable diff per plan step: semantic page skeleton + `<h1>` and
landmarks → hero (title, subtitle, author, blurb, cover) → "What you'll learn" list + CTA →
responsive styles → the accessibility and responsive tests. Each tick does one slice, states its
intent, and writes what it did back to the thread. You are no longer driving the implementation.

### 4. Verify & Recover
After each slice, `verify` runs lint and the checks. The criterion mapping stays live — including
a **fixture-locked layout test** that asserts no horizontal overflow at 375px and 1280px, turning
"responsive" from a hope into a wall the loop cannot climb over.

Then an accessibility check goes red — the CTA button's contrast ratio falls below the threshold.
**You are not pinged.** The next tick reads the failing check through the MCP connector, darkens
the button colour to clear the contrast bar (consistent with the assumptions still recorded in the
thread), re-runs, and goes green. The fix is just another iteration of the same loop; you never
copy an error into a prompt by hand.

### 5. Complete — **GATE 2**
The PR body carries the four acceptance boxes, each linking to evidence. The verifier's
done-condition job **refuses to pass while any `- [ ]` remains unchecked** — so the loop physically
cannot declare itself finished early. When all four are checked and CI is green, the loop posts
that it is ready and stops:

> *"Reconstructed state: 4 / 4 checked, verify pass, done-condition pass, PR MERGEABLE. The loop is
> ready for the merge gate — it will not merge autonomously."*

You click **merge.** Your second and final intervention.

## What it shipped, and what it cost you

**What it shipped:** a single self-contained `index.html` launch page — hero with title, subtitle,
author and blurb, a cover placeholder with proper `alt` text, a "What you'll learn" list, and a
"Get the book" CTA — responsive with no overflow at mobile or desktop widths, accessible, and behind
a green pipeline; assembled across several slices, one red accessibility check, and zero context
lost between them.

**What it cost you:** *approve the plan, click merge.* Two interventions. Everything between — the
slices, the failing contrast check, the recovery — was absorbed by the loop with unbroken memory in
the thread.

And because **no primitive mentions "landing page" or "book,"** the same loop that shipped issue #4
is the loop that shipped issue #1 (the conversational trip planner in the same repo, where you can
watch the done-condition gate flip from *4 unchecked → blocked* to *4 checked → mergeable*) and the
loop that will carry tomorrow's issue, unchanged. You built the loop once; every future feature
rides the same rails.

> **Reproduce it:** open the companion repo — **<https://github.com/Valentina-Alto/loop-engineering-test>** —
> file an issue from the **🔁 Feature Loop** template, then run the `/loop` command above. You will
> feel the difference between prompting an agent and *engineering the loop that prompts it.*
