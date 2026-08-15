# Chapter 5 — Governance: From Stochastic to Deterministic Agentic Development

Companion assets for **Chapter 5: Governance** from *From Vibe Coding to Enterprise Agentic Development*.

Chapter 5 treats governance as **engineering, not policy**. The moment an agent writes production code, three questions follow: *who is accountable, what can the agent actually do, and how do we prove what happened?* The chapter answers them by moving the agentic stack along a spectrum from **stochastic to deterministic**, using an instruction hierarchy, hooks, policy-as-code, deterministic parallel coordination, and a tamper-evident audit trail — anchored to external frameworks (NIST AI RMF, ISO/IEC 42001, the EU AI Act, the Microsoft Responsible AI Standard, OWASP/MITRE).

## 🎮 Interactive Chapter Experience

A single-view, gamified landing page (XP, achievements, progress tracking, light/dark theme):

- **The Stochastic-to-Deterministic Spectrum** — an interactive 5-band model; click each band to see where it lives between "same input, different output" and "same input, same output."
- **Five Governance Layers** — expandable cards for the Instruction Hierarchy, Hooks, Policy-as-Code, Parallel Agents, and the Audit Trail.
- **Decision Boundaries** — the four tiers (Forbidden → Human approval → Logged & reviewable → Fully autonomous).
- **External Frameworks** — how the five layers map onto NIST, ISO 42001, the EU AI Act, the Microsoft RAI Standard, and OWASP/MITRE.
- **Knowledge Check & Achievements** — quizzes and unlockables to reinforce the concepts.

➡️ **[Launch the Chapter 5 Interactive Experience](https://valentina-alto.github.io/Enterprise-Vibe-Coding-for-Agentic-AI/chapter5/chapter5-landing.html)**

> If the link above is not yet live, enable GitHub Pages on this repository (Settings → Pages → deploy from the `main` branch, root) and the page will be served from `chapter5/`.

## Concepts in This Chapter

| Concept | Summary |
|---------|---------|
| Stochastic → Deterministic Spectrum | Five bands from raw LLM generation to fully deterministic CI gates; push consequential actions toward the deterministic end. |
| Layer 1 — Instruction Hierarchy | Tier 1 global rules (`.github/copilot-instructions.md`), Tier 2 scoped instructions (`applyTo` globs), Tier 3 memory (`.memory.md`). |
| Layer 2 — Hooks | Deterministic side-channels under `.github/hooks/` that block actions before they run; scaled up as agentic workflows in `.github/workflows/`. |
| Layer 3 — Policy-as-Code | Declarative, testable, auditable, versioned rules (OPA/Rego) inherited org-wide. |
| Layer 4 — Parallel Agents | Determinism through disjoint scopes, idempotency, and file-mediated coordination. |
| Layer 5 — Audit Trail | Unbroken causal chain, attributable identity, tamper-evident storage. |
| Decision Boundaries | Tier 0 Forbidden · Tier 1 Human approval · Tier 2 Logged & reviewable · Tier 3 Fully autonomous. |

## Files

- [chapter5-landing.html](chapter5-landing.html) — Interactive, gamified chapter landing page (single-view recap). Self-contained, no build step required.
