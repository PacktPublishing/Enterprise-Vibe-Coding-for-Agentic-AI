# Copilot Instructions — Engineering Standards

These instructions apply to all code generated or modified in this repository. Follow them by default; deviate only when the user explicitly requests otherwise.

## Stack

- **Backend:** Python with [FastAPI](https://fastapi.tiangolo.com/).
- **Frontend:** [React](https://react.dev/).

Use idiomatic patterns for each framework (FastAPI dependency injection, Pydantic models, React function components with hooks).

## Repository Structure

The codebase is organised into three top-level folders. Place new files in the correct folder and respect the boundary between them.

- `frontend/` — React application (UI, components, client-side routing, styling).
- `backend/` — FastAPI service (routes, services, models, persistence).
- `infra/` — Infrastructure as code, deployment manifests, environment configuration.

Cross-folder imports are not allowed: the frontend talks to the backend over HTTP only, and `infra/` is consumed by deployment tooling, not application code.

## UI Guidelines

- **Dark mode is mandatory.** Every screen, component, and new UI element must render correctly in both light and dark themes. Use theme tokens / CSS variables rather than hardcoded colours.
- **Use shared design components.** Before creating a new component, check `frontend/` for an existing one. Extend the shared library rather than duplicating styles.
- **Prefer responsive layouts.** Use fluid grids, flexbox, and relative units. Designs must work from mobile widths up to desktop without horizontal scrolling.

## Coding Rules

- **Prefer async APIs.** Use `async def` for FastAPI route handlers and any I/O-bound work. On the frontend, prefer `async/await` over chained `.then()` calls.
- **Keep business logic outside routes.** FastAPI route handlers should validate input, call a service-layer function, and return a response. Domain logic, persistence, and external integrations belong in dedicated service modules under `backend/`.
- **Never hardcode secrets.** API keys, connection strings, tokens, and credentials must be read from environment variables or a secrets manager. Do not commit `.env` files containing real values, and do not inline secrets in source, tests, or infrastructure templates.
