# Post-Billing Staging Env

Use this after billing/auth/provider access is restored.

## Purpose

The normal staging examples are intentionally safe for no-billing work: auth disabled, billing disabled, fake provider, and sandbox Try-On generation.

For paid live acceptance, use the production-like override template:

```powershell
Copy-Item .env.post-billing-staging.example .env.post-billing-staging.local
```

Replace all `replace-with-real-*` and `replace-with-*` values with real staging secrets before deploy.

The `.example` file is not deployable by itself. It should be blocked by the production gate until copied to `.local` and filled with real values.

## Required Gate

Run from the repository root:

```powershell
.venv\Scripts\python.exe scripts\production_infrastructure_readiness_gate.py `
  --env-file .env.post-billing-staging.local `
  --require-production
```

Expected:

- `readiness_status` is `ready`;
- `failed_checks` is empty;
- auth, billing, Redis, PostgreSQL, S3 object storage, live LLM, live Try-On, and unsafe fallback checks pass.

Do not run paid Try-On, Product Card, Similar Search garment-photo, or AI category validation acceptance until this gate is ready.
