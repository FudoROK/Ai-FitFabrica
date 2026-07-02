# AI FitFabrica Project Structure

## Purpose

This document gives a concise structural map of the repository.

It is intentionally high level. The exact file-level source of truth is the repository tree itself.

## Repository Layout

### `src/`

Primary backend code.

Key contours:

- `src/entrypoints/`: FastAPI routes, runtime wiring, status and public backend ingress
- `src/domain/`: typed business models, policies, and provider-neutral contracts
- `src/use_cases/`: workflow orchestration and backend application services
- `src/adapters/`: integrations with SQL, cache, storage, vector search, AI, and external systems
- `src/runtime_agents/`: backend-owned runtime task contours
- `src/adk_agents/`: structured-output agent role packages
- `src/use_cases/agents/`: canonical backend-owned agent invocation service and ports
- `src/adapters/agents/`: provider gateway and isolated test audit adapter

### `tests/`

Repository verification:

- business behavior tests
- route tests
- architecture guardrails
- provider/runtime tests
- workflow regression coverage

### `apps/web/`

Next.js frontend application.

Expected structure inside the web app:

- routes/pages
- workspace flows
- shared UI components
- typed API usage
- thin-client state handling

### `docs/`

Project documentation.

Active truth lives in the top-level documentation files.
Historical plans and specs live under `docs/superpowers/`.

### `scripts/`

Project maintenance and verification helpers, including architecture checks.

## Architectural Reading Order

For someone entering the project, the recommended reading order is:

1. `README.md`
2. `docs/current_system_full_documentation.md`
3. `docs/backend_file_catalog.md`
4. `docs/frontend_file_catalog.md`
5. `docs/refactor_status_2026-06-13.md`

## Structure Rules

The current repository direction is:

- backend-first
- thin frontend client
- typed contracts
- one canonical gateway for all product-agent invocations
- provider-neutral workflow ports so Gemini/Vertex, OpenAI, Anthropic, or local runtimes can be replaced behind adapters
- isolated adapters
- small, decomposed modules instead of oversized files

Support-only or compatibility contours may still exist in a few backend areas, but active product work should follow the current portable baseline rather than older runtime patterns.
