# No-Billing Local Acceptance Gate

Use this gate while provider billing is unavailable. It verifies that the project remains testable without paid AI calls.

## List Checks

```powershell
.venv\Scripts\python.exe scripts\no_billing_acceptance_gate.py --list
```

This prints the exact backend, frontend, architecture, compile, and readiness commands.

## Run Standard Gate

```powershell
.venv\Scripts\python.exe scripts\no_billing_acceptance_gate.py
```

Expected:

- `readiness_status` is `ready`;
- `failed_checks` is empty;
- frontend `typecheck`, `lint`, and `build` pass;
- no paid provider calls are made.

## Faster Local Pass

```powershell
.venv\Scripts\python.exe scripts\no_billing_acceptance_gate.py --skip-frontend-build
```

Use this while iterating on backend/frontend guardrails. Run the standard gate before handoff.

## Full Backend Pass

```powershell
.venv\Scripts\python.exe scripts\no_billing_acceptance_gate.py --full-backend
```

Use this before a deployment handoff or when backend shared contracts changed.
