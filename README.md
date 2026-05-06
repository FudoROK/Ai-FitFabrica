# AI Assistant Backend Skeleton Baseline

This repository serves as a clean, neutral, and production-ready skeleton baseline for new client AI Assistant projects. It provides a deployable end-to-end runtime contour, allowing new client projects to quickly bootstrap and focus on adding client-specific logic, fields, integrations, and channels.

## Core Principles

*   **Deployable Day 0:** Fully functional and deployable from the start.
*   **Neutral:** Free from client-specific branding, prompts, or logic.
*   **Backend-First:** All business logic, computations, and security are encapsulated in the backend.
*   **Pluggable Adapters:** Easy to swap integrations (CRMs, messaging channels, LLM providers).
*   **Client Independent:** Each client copy is isolated, with separate GitHub, GCP projects, and secrets.
*   **Forward-Only Extension:** Designed for adding new features, not cleaning up legacy.

## Event Pipeline (Day 0 Baseline)

`Telegram -> Webhook -> Pub/Sub -> Backend -> Primary Agent -> Firestore -> Reply -> Telegram`

## Architectural Constraints

*   Backend orchestrates all side effects.
*   LLM is compute-only and returns strictly `reply_text` and `system_payload`.
*   Domain logic is strictly separated by layers: `entrypoints / use_cases / domain / adapters / runtime_agents / adk_agents`.
*   Agents do not orchestrate each other; the backend is the sole orchestrator.

## Project Documentation

*   `docs/plan.md` — Detailed implementation plan for this skeleton baseline.
*   `docs/bootstrap_checklist.md` — A checklist for bootstrapping a new client project from this skeleton.
*   `docs/env_setup_guide.md` — Guide for setting up environment variables and secrets.
*   `docs/deploy_guide.md` — Instructions for deploying the skeleton backend to Google Cloud.
*   `docs/day0_smoke_test_guide.md` — Guide for performing essential smoke tests on day 0.
*   `docs/core_optional_client_boundaries.md` — Defines what is considered core, optional, and client-specific.

## Local Setup (Python 3.11)

```bash
bash scripts/setup_test_env.sh
source .venv/bin/activate
cp .env.example .env
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## Validation

```bash
bash scripts/run_tests.sh
python scripts/check_architecture.py
python -m compileall src
```
