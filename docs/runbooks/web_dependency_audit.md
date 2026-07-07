# Web Dependency Audit

Use this audit during no-billing local acceptance and before post-billing paid workflow testing.

## Purpose

The audit records npm dependency vulnerability evidence for the Next.js frontend.

Policy:

- `high` and `critical` findings block readiness;
- `low` and `moderate` findings are reported as evidence and do not block the local pre-billing gate;
- unparseable or failed npm audit output fails closed.

## Local Command

Run from the repository root:

```powershell
.venv\Scripts\python.exe scripts\web_dependency_audit.py --require-ready
```

Expected:

- `gate` is `web_dependency_audit`;
- `readiness_status` is `ready`;
- `failed_checks` is empty;
- `checks.npm_audit.vulnerabilities` contains the current npm audit counts.

## Failure Policy

If the audit returns `blocked`, do not start paid workflow acceptance until the dependency issue is reviewed.

For `high` or `critical` findings:

- upgrade the affected package when the upgrade is compatible with the current Next.js stack;
- avoid browser-side workarounds for vulnerable dependencies;
- rerun frontend `lint`, `typecheck`, `build`, and the no-billing acceptance gate after changes.
