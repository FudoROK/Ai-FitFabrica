---
name: repo-validation
description: Use when validating, testing, or reviewing changes in the AI Assistant skeleton baseline. Runs the repo-local validation workflow and reports exactly what passed, failed, or was not run.
---

# Repo Validation

Run the repo-local validation workflow when a task changes runtime code, contracts, docs, or deployment configuration.

## Commands

Default validation:

```powershell
powershell -ExecutionPolicy Bypass -File .\plugins\ai-assistant-skeleton\scripts\validate_repo.ps1
```

Single-test validation:

```powershell
powershell -ExecutionPolicy Bypass -File .\plugins\ai-assistant-skeleton\scripts\validate_repo.ps1 -PytestArgs tests\path\to\test_file.py
```
