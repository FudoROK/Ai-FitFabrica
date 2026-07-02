# Try-On Parallel Analysis Bundle Design

## Goal

Make Human Identity, Garment Identity, and Material / Texture mandatory persisted backend stages before Try-On generation.

## Architecture

`TryOnAnalysisBundleService` owns parallel execution of three provider-neutral analysis ports. Production adapters invoke agents only through `AgentInvocationService`; isolated tests use deterministic adapters.

The Try-On workflow:

1. validates and persists uploads;
2. marks the job as analyzing;
3. runs Human Identity, Garment Identity, and Material / Texture concurrently;
4. validates and persists all three snapshots on the Try-On job aggregate;
5. continues to generation only when all required analyses pass backend policy.

Agents do not call each other, persist state, choose workflow transitions, or charge credits.

## Persistence

PostgreSQL stores each analysis as a separate one-to-one child entity:

- `try_on_human_identity_analyses`;
- `try_on_garment_identity_analyses`;
- `try_on_material_texture_analyses`.

The agent invocation ledger remains the source of provider/model/latency audit metadata.

## Failure Policy

- Missing artifact, provider failure, invalid contract output, low confidence, or high uncertainty fails the analysis bundle closed.
- Human Identity backend verdict must be `allowed`.
- Garment Identity must meet configured minimum confidence and must not have high uncertainty.
- Material / Texture must meet configured minimum confidence, must not have high uncertainty, and cannot claim exact composition without trusted evidence.
- Any required-analysis failure marks the Try-On job failed, blocks generation, and records zero charged credits.

## Scope

This slice does not add Try-On Instruction Agent, real generation activation, model-backed Quality Verifier Agent, or Repair Agent orchestration. Those remain subsequent Wave 3 slices.

