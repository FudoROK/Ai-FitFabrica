# Production Fallback Usage Audit

Use this guardrail before post-billing staging acceptance and during no-billing local acceptance.

## Purpose

The audit prevents silent expansion of runtime fallback paths in customer-facing backend builders.

It scans reviewed runtime entrypoint files for fallback-risk tokens:

- `InMemory`
- `in_memory`
- `Fake`
- `sandbox_fake`
- `stub_image_editing`
- `stub`

Existing reviewed fallback references are allowed for local, sandbox, and pre-billing workflows. New references block the gate until they are reviewed and either removed or deliberately added to the reviewed maximum counts.

## Local Command

Run from the repository root:

```powershell
.venv\Scripts\python.exe scripts\production_fallback_usage_audit.py --require-ready
```

Expected:

- `gate` is `production_fallback_usage_audit`;
- `readiness_status` is `ready`;
- `failed_checks` is empty.

## Failure Policy

If the gate returns `blocked`, do not start paid workflow acceptance.

Review the failed file and confirm whether the new fallback reference is:

- test-only or local-only and safely isolated;
- required for no-billing development but blocked by production env gates;
- accidental production risk and should be removed.

Only update `REVIEWED_MAX_COUNTS` in `scripts/production_fallback_usage_audit.py` after explicit review.
