# Chapter 4 — Reshaping the SDLC: Agentic DevOps and the RPI Cadence in Practice

Companion assets for **Chapter 4: Reshaping the SDLC** from *From Vibe Coding to Enterprise Agentic Development*.

Chapter 4 puts the six primitives (Instructions, Prompts, Agents, Skills, Hooks, MCP) to work across the full software lifecycle — **Plan → Design → Develop → Test → Release → Maintain** — through a single running scenario: **FlowDesk**, an agentic IT service copilot for Northwind Logistics. It introduces the **RPI cadence** (Research → Plan → Implement) that runs inside every phase, and defines **Agentic DevOps** as the through-line that ties all phases together.

## 🎮 Interactive Chapter Experience

A two-tab gamified landing page:

1. **Chapter Recap** — Explore the six SDLC phases reimagined with primitives, the RPI cadence, Agentic DevOps principles, quizzes, and achievements.
2. **Primitives Repo** — An interactive, expandable repository explorer showing every primitive file from this chapter (agents, skills, prompts, hooks, MCP config) with descriptions and key excerpts.

➡️ **[Launch the Chapter 4 Interactive Experience](https://valentina-alto.github.io/Enterprise-Vibe-Coding-for-Agentic-AI/chapter4/chapter4-landing.html)**

> If the link above is not yet live, enable GitHub Pages on this repository (Settings → Pages → deploy from the `main` branch, root) and the page will be served from `chapter4/`.

## Primitives in This Chapter

| Type | File | Purpose |
|------|------|---------|
| Instructions | `copilot-instruction.md` | Repository-wide engineering standards |
| Agent | `backend-dev.agent.md` | Backend development specialist (scoped to `backend/`) |
| Agent | `infra-dev.agent.md` | Infrastructure-as-code specialist (scoped to `infra/`) |
| Agent | `test-dev.agent.md` | Test engineer (unit, integration, contract) |
| Agent | `scenario-test-author.agent.md` | Agent flow trace-test specialist |
| Agent | `release-captain.agent.md` | Release coordinator with anomaly detection |
| Skill | `agent-framework-scaffold/SKILL.md` | Multi-agent app scaffolding template |
| Prompt | `meeting-transcript-to-spec.prompt.md` | Meeting transcript → structured spec |
| Prompt | `scaffold-microservice.prompt.md` | One-line → full microservice scaffold |
| Prompt | `boq-and-cost-estimation.prompt.md` | Architecture → Azure BoQ + cost estimate |
| Prompt | `spec-to-architecture-diagram.prompt.md` | Spec → Mermaid architecture diagrams |
| Prompt | `spec-to-test-plan.prompt.md` | User story → 7-case test plan (RPI gate) |
| Hook | `secrets-scanner/` | Gitleaks secret scan on release-captain actions |
| MCP | `.vscode/mcp.json` | Mermaid + Azure DevOps MCP server config |

## Files

- [chapter4-landing.html](chapter4-landing.html) — Interactive, gamified chapter landing page with two tabs: chapter recap and primitives repository explorer. Self-contained, no build step required.
- [.github/](./.github/) — All primitive files referenced in Chapter 4
- [.vscode/mcp.json](.vscode/mcp.json) — MCP server configuration
