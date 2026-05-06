---
name: repo-architecture-guard
description: Use when a task changes architecture, refactors backend flows, touches memory-related code, or needs a repo-specific layer or split check in the AI Assistant skeleton baseline.
---

# Repo Architecture Guard

Use this skill when a change risks violating the baseline architecture.

## Guardrails

- `primary_agent`, `daily_memory_agent`, and `rolling_memory_agent` stay independent.
- Backend remains the only orchestrator for side effects.
- Daily and rolling memory stay split.
- Firestore access stays behind repository and adapter boundaries.

## Forbidden Legacy Patterns

- reintroducing client-specific branding into baseline core
- merging daily and rolling memory into one runtime payload
- adding direct side effects inside agent definitions
