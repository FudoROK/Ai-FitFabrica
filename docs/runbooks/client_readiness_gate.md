# B2C/B2B Client Readiness Gate

Use this gate before enabling billing to confirm that all customer-facing B2C and B2B contours are locally prepared.

```powershell
.venv\Scripts\python.exe scripts\client_readiness_gate.py
```

Expected:

- `readiness_status` is `ready`;
- `failed_checks` is empty;
- every flow in `flows` has `status=passed`.

The gate does not claim live customer production readiness. It keeps the remaining external blockers explicit:

- production auth activation;
- billing core activation;
- live AI/provider acceptance;
- approved marketplace source activation;
- deployed staging browser acceptance.

After this gate passes, run:

```powershell
.venv\Scripts\python.exe scripts\no_billing_acceptance_gate.py --full-backend
.venv\Scripts\python.exe scripts\staging_no_billing_smoke.py `
  --api-base-url "https://api.fit.aisoulfabrica.com" `
  --web-base-url "https://fit.aisoulfabrica.com" `
  --status-token "<STATUS_ENDPOINT_TOKEN>"
```

After billing/auth/provider access is restored, run the post-billing gate and paid live acceptance.
