# Refactor Status 2026-06-13

This note records the latest structural cleanup completed on `2026-06-13`.

## Runtime wiring

- `src/entrypoints/runtime_dependencies.py` remains the stable public runtime entrypoint.
- Runtime wiring is split across:
- `src/entrypoints/runtime_dependency_contracts.py`
- `src/entrypoints/runtime_dependency_builders.py`
- `src/entrypoints/runtime_dependency_foundation_builders.py`
- `src/entrypoints/runtime_dependency_workflow_builders.py`
- `src/entrypoints/runtime_dependency_operations_builders.py`

## Identity runtime repositories

- `src/identity_core/services/identity_core_runtime_repositories.py` is now a facade.
- Test-only in-memory implementations are isolated in focused modules:
- `src/identity_core/services/identity_core_runtime_repositories_inmemory.py`
- `src/identity_core/services/identity_core_runtime_repository_helpers.py`

## Memory layer

- `src/memory_layer/service.py` is now a thin facade under the 300-line target.
- Its responsibilities are split into:
- `src/memory_layer/service_read_bundle.py`
- `src/memory_layer/service_windowing.py`
- `src/memory_layer/service_state_updates.py`
- `src/memory_layer/service_operations.py`

- `src/memory_layer/run_ledger_repository.py` is now a stable facade.
- Ledger logic is split into:
- `src/memory_layer/run_ledger_shared.py`
- `src/memory_layer/run_ledger_firestore.py`
- `src/memory_layer/run_ledger_inmemory.py`

- `src/memory_layer/services/memory_summary_service.py` now delegates to helper modules:
- `src/memory_layer/services/memory_summary_models.py`
- `src/memory_layer/services/memory_summary_windowing.py`
- `src/memory_layer/services/memory_summary_runtime_factory.py`
- `src/memory_layer/services/memory_summary_candidate_collection.py`
- `src/memory_layer/services/memory_summary_active_window_runner.py`

- `src/memory_layer/services/memory_sync_persistence_service.py` is now a thinner facade under the 300-line target.
- Persistence helpers are split into:
- `src/memory_layer/services/memory_sync_persistence_models.py`
- `src/memory_layer/services/memory_sync_persistence_rolling.py`
- `src/memory_layer/services/memory_sync_persistence_state.py`

## Provider and workflow cleanup

- `src/adapters/database/firestore/event_state_machine.py` is now a stable facade under the 300-line target.
- Its transition/config helpers are split into:
- `src/adapters/database/firestore/event_state_machine_config.py`
- `src/adapters/database/firestore/event_state_machine_models.py`
- `src/adapters/database/firestore/event_state_machine_helpers.py`
- `src/adapters/database/firestore/event_state_machine_transitions.py`

- `src/llm/providers/gemini_structured_provider.py` is now a facade under the 300-line target.
- Gemini structured provider logic is split into:
- `src/llm/providers/gemini_structured_models.py`
- `src/llm/providers/gemini_structured_client.py`
- `src/llm/providers/gemini_structured_schema.py`
- `src/llm/providers/gemini_structured_payloads.py`

- `src/llm/tasks/__init__.py` no longer eager-imports task modules, which removes a real circular-import startup risk in the memory-agent task path.

- `src/use_cases/try_on/workflow_service.py` is now a 169-line facade.
- Try-On workflow responsibilities are split into:
- `src/use_cases/try_on/workflow_models.py`
- `src/use_cases/try_on/workflow_upload_validation.py`
- `src/use_cases/try_on/workflow_job_factory.py`
- `src/use_cases/try_on/workflow_execution.py`
- Legacy Try-On Firestore/GCS storage adapters have been removed from the active tree.

- `src/adapters/database/sql/identity_repositories.py` is now a thinner facade.
- SQL identity helpers are split into:
- `src/adapters/database/sql/identity_repository_mapping.py`
- `src/adapters/database/sql/identity_repository_mutations.py`

- `src/entrypoints/runtime_dependencies.py` remains the stable public runtime entrypoint and is now reduced to 282 lines.
- Shared cache and lazy-factory helpers are split into:
- `src/entrypoints/runtime_dependency_cache.py`
- `src/entrypoints/runtime_dependency_lazy_factories.py`
- `src/entrypoints/runtime_dependency_contracts.py` now types the FitFabrica product-agent bundle with `BaseAgent` roots instead of `Any`.
- Identity runtime wiring now allows only SQL for normal runtime and in-memory repositories for test mode; the old Firestore fallback has been removed.
- `src/services/rate_limit/firestore_rate_limiter.py` has been removed because the active rate-limit factory already supports only Redis and in-memory backends.
- The legacy internal `/tasks/memory-summary` route and its dedicated runtime container have been removed from the active HTTP surface.

- The legacy dialog/context service assembly layer has been removed from the active repository contour.

## Verification

Verified on `2026-06-13`:

- `scripts/check_architecture.py` passed
- `python -m compileall src` passed
- `python -m pytest -q -x --maxfail=1` passed with `662 passed`
- `npm run lint` in `apps/web` passed
- `npm run typecheck` in `apps/web` passed
- `npm run build` in `apps/web` passed
- targeted runtime/dialog regression suites passed after the latest container and typing cleanup

## Remaining attention areas

- No Python files under `src/` remain above the 300-line decomposition target.
- The next cleanup pass should focus on repo hygiene and documentation cleanup, not structural oversized-file remediation.
