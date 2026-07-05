# Production Auth Readiness Gate

Use this gate before enabling billing to confirm that public auth is safely prepared and still fail-closed until the production provider is activated.

```powershell
.venv\Scripts\python.exe scripts\auth_readiness_gate.py
```

Expected before auth activation:

- `readiness_status` is `ready`;
- `AUTH_PROVIDER=disabled` is documented in env examples;
- `/auth/sign-in` returns structured `503 auth_not_configured`;
- `/auth/session` returns `authenticated=false` and `auth_configured=false`;
- `/auth/logout` is idempotent and clears `fitfabrica_session`;
- frontend checks `/auth/session` before trying sign-in;
- frontend does not present fake OAuth/session success.

The remaining external blocker is `production_auth_provider_activation`.

After production auth is connected, update this gate and the public auth tests to require the real provider/session behavior instead of fail-closed behavior.
