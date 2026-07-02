# Product Card Garment Identity Design

## Goal

Make Garment Identity a mandatory, persisted backend stage before Product Card generation and verify the complete workflow against the real staging Gemini runtime.

## Architecture

`ProductCardWorkflowService` orchestrates two provider-neutral ports:

1. `GarmentIdentityAnalysisPort` analyzes the first canonical product image.
2. The backend validates and persists a `ProductCardGarmentAnalysis`.
3. `ProductCardGenerationPort` receives only the persisted structured analysis and approved request metadata.
4. The Product Card Agent creates marketplace content without re-interpreting the image.

Provider SDKs remain behind the canonical `AgentInvocationService`. Product Card domain, workflow, persistence, and routes remain independent from Gemini and Vertex.

## Persistence

PostgreSQL stores one `product_card_garment_analyses` row per Product Card job. The row contains:

- job and invocation identifiers;
- prompt and contract versions;
- garment type, colors, silhouette, preserved details, and typed visual details;
- evidence, confidence, uncertainty, unknowns, and limitations;
- completion timestamp.

The canonical agent invocation ledger remains the source of provider/model/latency audit metadata.

## Runtime Policy

- `environment=test`: deterministic Garment Identity adapter and Product Card generation fake.
- Any non-test environment: both stages use canonical agent invocation.
- Missing artifact, provider failure, invalid contract output, high uncertainty, or confidence below the configured minimum fails the Product Card job closed.
- Product Card generation does not start if Garment Identity fails.
- Completion credits are charged only after analysis persistence, generated version persistence, and completed job state.

## API

- Existing create/status/result endpoints remain compatible.
- `GET /api/product-cards/{job_id}/garment-analysis` returns the saved validated garment analysis.
- Provider internals, prompts, image bytes, and temporary URLs are never exposed.

## Verification

- TDD coverage for domain model, adapter, persistence, orchestration, runtime wiring, routes, migration, and architecture guardrails.
- Full backend and frontend regression gates.
- Staging migration and real Gemini smoke proving two successful invocations in order: `garment_identity_agent`, then `product_card_agent`.
