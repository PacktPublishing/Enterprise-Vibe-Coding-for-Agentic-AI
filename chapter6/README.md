# Chapter 6 — Use Cases: Building Agentic Solutions with the HVE Primitives

Companion assets for **Chapter 6: Use Cases** from *Agentic Development in Practice*.

Chapter 6 presents three complete agentic products built in different domains, demonstrating how HVE primitives come together to deliver enterprise-grade solutions:

1. **Travel Agency (SkyBridge Travel)** — Multi-agent orchestration via Handoff pattern. A concierge routes to flight/hotel specialists while presenting one seamless conversation.
2. **Conversational Shopping (Luxe)** — Decision support meets commerce. An AI personal shopper guides purchases within well-defined boundaries.
3. **Multi-Channel Marketing (SkillForge)** — Content production + governance at scale via a sequential pipeline generating email, Instagram, TikTok, and LinkedIn campaigns.

## 🎮 Interactive Chapter Experience

A two-tab gamified landing page:

1. **Use Cases** — Explore all three use cases with business context, orchestration patterns, embedded video demos, and clickable primitives.
2. **Primitives Repo** — An interactive repository tree with use-case filters. Highlight which primitives are used by each project. Click to see descriptions and key code excerpts.

➡️ **[Launch the Chapter 6 Interactive Experience](https://valentinaalto.github.io/agentic-development-in-practice/code-and-assets/chapter6/chapter6-landing.html)**

## Projects in This Chapter

### ✈️ Travel Agency
| Component | Description |
|-----------|-------------|
| `travel agency/app.py` | Flask app with MAF Handoff workflow |
| `travel agency/agents/triage_agent.py` | Concierge / conversation router |
| `travel agency/agents/flight_agent.py` | Flight specialist (AviationStack API) |
| `travel agency/agents/hotel_agent.py` | Hotel specialist (mock data) |

### 🛍️ Conversational Shopping
| Component | Description |
|-----------|-------------|
| `conversational shopping/app.py` | Flask + SSE chat endpoint |
| `conversational shopping/agents/shopping_assistant.py` | AI personal shopper |
| `conversational shopping/mock_data.py` | 12-product catalog |

### 📣 CMO Marketing Campaign
| Component | Description |
|-----------|-------------|
| `cmo-marketing-campaign/app.py` | Flask + Sequential pipeline |
| `cmo-marketing-campaign/agents/` | 8 agents: strategy, content, audience, performance + 4 channel adapters |

## Primitives

| Type | File | Used By |
|------|------|---------|
| Skill | `maf-orchestration-patterns/SKILL.md` | ✈️ Travel |
| Skill | `marketing-workflow-agents/SKILL.md` | 📣 Marketing |
| Prompt | `specialist-agent.prompt.md` | ✈️ Travel |
| Prompt | `campaign-brief-to-workflow.prompt.md` | 📣 Marketing |
| Agent | `shopping-tester.agent.md` | 🛍️ Shopping |
| Hook | `catalog-schema-guard.json` + `catalog_schema_check.py` | 🛍️ Shopping |
| MCP | `.vscode/mcp.json` | All |

## Files

- [chapter6-landing.html](chapter6-landing.html) — Interactive landing page with video demos and primitives explorer
- [travel agency/](./travel%20agency/) — Complete travel agent prototype
- [conversational shopping/](./conversational%20shopping/) — Complete shopping assistant prototype
- [cmo-marketing-campaign/](./cmo-marketing-campaign/) — Complete marketing campaign generator
