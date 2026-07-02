# Google Gen AI SDK Migration - 2026-06-15

## Scope

The direct structured Gemini provider was migrated from the deprecated Vertex AI generative modules to `google-genai==1.66.0`.

Removed production dependency path:

- `vertexai.generative_models.GenerativeModel`
- `vertexai.generative_models.GenerationConfig`
- `vertexai.generative_models.Part`

Active replacement path:

- `google.genai.Client(vertexai=True, project=..., location=...)`
- `client.models.generate_content(...)`
- `google.genai.types.GenerateContentConfig`
- `google.genai.types.Part.from_bytes(...)`

## Architecture

- `AgentInvocationService` remains the only production-agent invocation entry point.
- Workflows, use cases, routes, and domain code do not import Google SDKs.
- Provider-specific SDK calls remain isolated in `src/llm/providers/gemini_structured_client.py`.
- Existing provider-neutral ports, persisted agent audit records, and Product Card contracts are unchanged.

## Rollback

No database migration is involved. Rollback consists of restoring the previous API and worker container images if staging smoke validation fails.

## Verification

Required verification:

- Gemini structured provider text and multimodal tests
- provider runtime and routing tests
- AgentInvocationService and gateway tests
- architecture and lazy-loading guardrails
- full backend regression suite
- staging Gemini text and multimodal agent smoke

Local verification result on `2026-06-15`: `629 passed`.

Staging verification result:

- job: `product_card_1781528800675857`
- multimodal `garment_identity_agent`: `succeeded`, validation `passed`
- structured-text `product_card_agent`: `succeeded`, validation `passed`
- provider/model: `gemini_structured` / `gemini-2.5-flash`
- both invocations share the Product Card job trace ID
- API and worker remained healthy
- no deprecated Vertex AI generative-module warning appeared in runtime logs
