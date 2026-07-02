# Product Card Provider-Neutral Agent Design

## Goal

Replace the Product Card fake generation adapter in non-test environments with a production agent adapter while keeping workflows independent from Gemini, ADK, OpenAI, Anthropic, and local-model SDKs.

## Architecture

`ProductCardWorkflowService` continues to depend only on `ProductCardGenerationPort`.

The production `ProductCardAgentGenerationAdapter`:

1. Receives the domain request and stored asset keys.
2. Reads assets through the portable `ObjectStorage` contract.
3. Builds integrity-checked `AgentArtifactReference` values.
4. Invokes the canonical `AgentInvocationService`.
5. Validates `ProductCardContentContract`.
6. Maps the validated agent output into `ProductCardDraft`.

Provider selection remains behind `AgentInvocationPort` and `AgentRuntimePort`. Replacing Gemini with OpenAI, Anthropic, or a local runtime must require only a new provider adapter and configuration, not Product Card workflow changes.

## Runtime Policy

- `environment=test`: deterministic `FakeProductCardGenerationAdapter`.
- Any non-test environment: `ProductCardAgentGenerationAdapter`.
- Missing provider runtime, invalid agent output, missing artifacts, or provider failure: fail closed.
- Credits are charged only after a generated version is saved and the job is completed.
- Agent invocation metadata is persisted in the canonical audit ledger.

## Agent Contract

Input context contains only approved JSON metadata:

- title hint;
- category;
- target channel;
- brand tone;
- stored asset count.

Images are passed only as approved artifact references. Agent output remains strict JSON with title, short description, key attributes, merchandising notes, confidence, and limitations.

## Verification

- Adapter unit tests for request mapping, artifact references, output mapping, and safe failure.
- Runtime wiring tests proving fake is test-only and production uses the agent adapter.
- Existing Product Card workflow, route, architecture, frontend lint, typecheck, and build checks remain green.
