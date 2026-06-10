---
description: "Scaffold a standard backend microservice (FastAPI) under `backend/` from a one-line description: entry point, healthcheck, settings module, telemetry wiring, Dockerfile, and unit tests — following repository engineering standards in `.github/copilot-instruction.md`."
name: "Scaffold Backend Microservice"
agent: "Backend Developer"
argument-hint: "One-line description of the microservice (purpose + key data it owns)"
---

# Scaffold Backend Microservice

Generate a new backend microservice based on this one-line description from the user:

> **${input:description:One-line description of the microservice (e.g. \"orders service owning order lifecycle and persistence in Postgres\")}**

Follow the engineering standards in [.github/copilot-instruction.md](../copilot-instruction.md). Place all new code under `backend/<service-name>/` using the naming the description implies (lower-kebab-case). Do not touch `frontend/` or `infra/`.

## Required Deliverables

Produce the following files. Each must be runnable and minimal — no speculative features beyond what the description implies.

1. **Entry point** — `backend/<service-name>/main.py`
   - FastAPI app with a clear `app = FastAPI(title=..., version=...)`.
   - Wires settings, telemetry, and routers.
   - `async def` route handlers; route handlers stay thin and delegate to the service layer.

2. **Healthcheck** — `GET /health`
   - Returns `{"status": "ok"}` with HTTP 200 when the process is alive.
   - Also expose `GET /health/ready` that performs a lightweight readiness check (e.g. settings loaded, downstream client constructed) and returns 200/503 accordingly.

3. **Settings module** — `backend/<service-name>/settings.py`
   - Pydantic `BaseSettings` (or `pydantic-settings`) class loading from environment variables.
   - Strongly typed fields with sensible defaults for local dev.
   - **Never hardcode secrets.** Secrets must be env-var-driven; document the required vars in the README block or comments.

4. **Telemetry wiring** — `backend/<service-name>/telemetry.py`
   - Structured logging (JSON) configured at startup.
   - OpenTelemetry tracing wired into FastAPI (use `opentelemetry-instrumentation-fastapi`) with an OTLP exporter controlled by env var (e.g. `OTEL_EXPORTER_OTLP_ENDPOINT`); export is disabled cleanly when the env var is unset.
   - `main.py` calls a single `configure_telemetry(app, settings)` function.

5. **Dockerfile** — `backend/<service-name>/Dockerfile`
   - Multi-stage build: builder installs deps, final stage is slim.
   - Runs as a non-root user.
   - `EXPOSE` the service port, `CMD` runs `uvicorn` against the app.
   - Includes a `HEALTHCHECK` instruction hitting `/health`.

6. **Unit tests** — `backend/<service-name>/tests/`
   - `test_health.py` — covers `/health` and `/health/ready` (happy + degraded).
   - `test_settings.py` — covers required env vars, defaults, and validation errors.
   - At least one `test_<feature>.py` stub asserting the entry point boots and routes are registered.
   - Use `pytest` and FastAPI's `TestClient` (or `httpx.AsyncClient` for async tests).

7. **Supporting files**
   - `backend/<service-name>/requirements.txt` (or update the workspace lockfile if one is in use — match existing repo convention).
   - `backend/<service-name>/__init__.py`.
   - A short module-level docstring on `main.py` describing the service purpose.

## Architecture Rules (from repository standards)

- Keep business logic out of route handlers — put it in a `services/` submodule even if there is only one function today.
- Prefer `async def` for any I/O-bound work.
- Read all config from env vars; never inline secrets.
- Reuse shared utilities already present in `backend/` before adding new ones — search first.

## Procedure

1. **Search** `backend/` for existing services and pick up conventions (folder layout, settings pattern, telemetry helper, Dockerfile style). Match them rather than introducing new ones.
2. **Derive** a service name and short description from the user's one-line input.
3. **Generate** all deliverables above in a single pass.
4. **Validate locally**:
   - `pytest backend/<service-name>/tests` — all green.
   - `docker build -t <service-name>:dev backend/<service-name>` — succeeds.
   - `docker run --rm -p 8000:8000 <service-name>:dev` then `curl localhost:8000/health` returns 200 (or skip the run step if not feasible in this environment and note it).
5. **Report** using the standard Backend Developer status block: Changed, Tests, Local build, Escalations.

## Out of Scope (do not generate)

- Deployment manifests, Bicep, or CI workflow changes — those belong to the Infra Developer agent and release workflows.
- Frontend code.
- Database migrations beyond a trivial connection check, unless the one-line description explicitly calls for a schema.
- Authentication providers or MCP permission changes — escalate if the description requires them.
