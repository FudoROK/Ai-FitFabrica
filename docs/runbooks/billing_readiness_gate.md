# Billing Activation Readiness Gate

Use this gate before enabling billing to confirm that the billing contour is prepared but still disabled.

```powershell
.venv\Scripts\python.exe scripts\billing_readiness_gate.py
```

Expected before billing activation:

- `readiness_status` is `ready`;
- env examples keep `BILLING_CORE_ENABLED=false`;
- credit balance and ledger endpoints delegate to backend billing service;
- billing service writes idempotent ledger events;
- SQL repository prevents negative balances;
- frontend credits page only displays backend DTOs and does not calculate balances.

Remaining external blockers:

- `billing_core_activation`;
- `payment_provider_activation`.

Before turning billing on, run:

```powershell
.venv\Scripts\python.exe scripts/billing_readiness_gate.py
.venv\Scripts\python.exe scripts/no_billing_acceptance_gate.py --full-backend
```

After turning billing on, run the post-billing gate and record live charge/refund evidence in `docs/reports/YYYY-MM-DD-post-billing-live-acceptance.md`.
