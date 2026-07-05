# Post-Billing Acceptance Gate

Use this gate after Google/Gemini/Vertex billing and provider access are restored, before running paid workflow acceptance.

## Local Preflight

Run from the repository root:

```powershell
.venv\Scripts\python.exe scripts\post_billing_acceptance_gate.py
```

Expected:

- `readiness_status` is `ready`;
- `checks.local_artifacts.status` is `passed`;
- `checks.ready_endpoint.status` may be `skipped` when no deployed API URL is provided.

## Deployed Readiness Gate

Run against staging after backend deploy:

```powershell
.venv\Scripts\python.exe scripts\post_billing_acceptance_gate.py `
  --api-base-url "https://api.fit.aisoulfabrica.com" `
  --status-token "<STATUS_ENDPOINT_TOKEN>" `
  --require-ready
```

Expected:

- `readiness_status` is `ready`;
- `checks.ready_endpoint.status` is `passed`;
- `failed_checks` is empty.

If the gate returns `blocked`, do not run paid Try-On, Product Card, Similar Search garment-photo, or AI category validation acceptance until the blocker is fixed.

## Next Commands

After the gate is ready, run the command list emitted in `next_commands`:

```powershell
.venv\Scripts\python.exe scripts\platform_foundation_smoke.py --require-ready
.venv\Scripts\python.exe scripts\auth_readiness_gate.py
.venv\Scripts\python.exe scripts\billing_readiness_gate.py
.venv\Scripts\python.exe scripts\business_catalog_search_index_readiness.py --require-db
.venv\Scripts\python.exe scripts\try_on_real_activation_smoke.py --require-ready
.venv\Scripts\python.exe scripts\business_catalog_staging_smoke.py
```

Copy `docs/reports/templates/post_billing_live_acceptance_template.md` to `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md` and record the results there.
