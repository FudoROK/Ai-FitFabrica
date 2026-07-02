# Workflow Agent Cost Map v1

Date: 2026-06-16

Pricing source: official Google Gemini API pricing page, captured for `gemini-2.5-flash` and `gemini-2.5-flash-lite` on 2026-06-16: https://ai.google.dev/gemini-api/docs/pricing

Cost config version: `provider_prices.gemini.2026-06-16.v1`

This document is a first planning baseline. It separates provider cost, internal cost, and FitFabrica credits. It does not change production billing rules.

## Assumptions

- `gemini-2.5-flash` text/image/video input: `$0.30 / 1M tokens`.
- `gemini-2.5-flash` output: `$2.50 / 1M tokens`.
- Internal cost uses a 20% platform reserve over provider cost.
- Virtual try-on and model-photo generation use a configurable `$0.04` per generated output estimate until the exact production SKU is finalized.
- `1 credit = 50 KZT`; planning conversion uses `1 USD = 500 KZT`.

## Cost Map Table

| workflow_type | step_order | step_name | agent_name | provider | model | input_type | output_type | required | can_retry | can_repair | charged_to_user | free_if_failed | expected_input_tokens | expected_output_tokens | expected_image_inputs | expected_image_outputs | expected_provider_cost_usd | expected_internal_cost_usd | notes |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| try_on | 1 | human_identity_analysis | human_identity_agent | gemini | gemini-2.5-flash | image+text | json | yes | yes | no | no_if_blocked | yes | 10000 | 1000 | 1 | 0 | 0.005500 | 0.006600 | Blocks unsuitable human photos before generation. |
| try_on | 2 | garment_identity_analysis | garment_identity_agent | gemini | gemini-2.5-flash | image+text | json | yes | yes | no | no_if_failed | yes | 12000 | 1500 | 1 | 0 | 0.007350 | 0.008820 | Required before Try-On Instruction. |
| try_on | 3 | material_texture_analysis | material_texture_agent | gemini | gemini-2.5-flash | image+text | json | yes | yes | no | no_if_failed | yes | 8000 | 1000 | 1 | 0 | 0.004900 | 0.005880 | Must stay honest about visual-only material estimates. |
| try_on | 4 | try_on_instruction | try_on_agent | gemini | gemini-2.5-flash | json | json | yes | yes | no | no_if_failed | yes | 6000 | 1200 | 0 | 0 | 0.004800 | 0.005760 | Converts validated analyses to generation instruction. |
| try_on | 5 | virtual_try_on_generation | try_on_generation | google_vertex | virtual-try-on-estimate | image+json | image | yes | yes | yes | yes_if_success | yes | 0 | 0 | 2 | 1 | 0.040000 | 0.048000 | Configurable estimate until exact image-generation SKU is finalized. |
| try_on | 6 | quality_verification | quality_verifier_agent | gemini | gemini-2.5-flash | image+json | json | yes | yes | no | included | yes | 12000 | 1200 | 1 | 0 | 0.006600 | 0.007920 | User should not see failed quality result. |
| try_on | 7 | repair_instruction | repair_agent | gemini | gemini-2.5-flash | image+json | json | no | yes | yes | free_if_system_failure | yes | 8000 | 1200 | 1 | 0 | 0.005400 | 0.006480 | Repair analysis/instruction only; does not include image edit cost. |
| try_on | 8 | repair_image_generation | repair_image_generation | google_vertex | virtual-try-on-estimate | image+json | image | no | yes | yes | free_if_system_failure | yes | 0 | 0 | 1 | 1 | 0.040000 | 0.048000 | Separate image-edit/generation cost for repair. |
| try_on | 9 | second_quality_verifier | quality_verifier_agent | gemini | gemini-2.5-flash | image+json | json | no | yes | no | free_if_system_failure | yes | 10000 | 1200 | 1 | 0 | 0.006000 | 0.007200 | Second Quality Verifier after repair, free when repair is our quality failure. |
| try_on | 10 | stylist_advice | fashion_stylist_agent | gemini | gemini-2.5-flash | json | json | no | yes | no | yes_if_requested | no | 5000 | 1500 | 0 | 0 | 0.005250 | 0.006300 | Optional advice add-on. |
| product_card | 1 | garment_identity_analysis | garment_identity_agent | gemini | gemini-2.5-flash | image+text | json | yes | yes | no | no_if_failed | yes | 12000 | 1500 | 1 | 0 | 0.007350 | 0.008820 | Persisted reusable child analysis. |
| product_card | 2 | material_texture_analysis | material_texture_agent | gemini | gemini-2.5-flash | image+text | json | optional | yes | no | included | yes | 8000 | 1000 | 1 | 0 | 0.004900 | 0.005880 | Optional for richer card facts. |
| product_card | 3 | product_card_generation | product_card_agent | gemini | gemini-2.5-flash | json | json | yes | yes | no | yes_if_success | yes | 9000 | 2500 | 0 | 0 | 0.008950 | 0.010740 | Uses structured garment analysis, not raw image reinterpretation. |
| product_card | 4 | pricing_recommendation | pricing_agent | gemini | gemini-2.5-flash | json | json | optional | yes | no | yes_if_requested | no | 7000 | 1800 | 0 | 0 | 0.006600 | 0.007920 | Optional price positioning. |
| product_card | 5 | model_photo_generation | product_image_generation | google_vertex | virtual-try-on-estimate | image+json | image | optional | yes | yes | yes_if_requested | yes | 0 | 0 | 1 | 1 | 0.040000 | 0.048000 | Optional generated visual asset. |
| product_card | 6 | quality_verification | quality_verifier_agent | gemini | gemini-2.5-flash | image+json | json | optional | yes | no | included | yes | 10000 | 1200 | 1 | 0 | 0.006000 | 0.007200 | Required for generated visuals. |
| similar_search | 1 | garment_identity_or_parser | garment_identity_agent | gemini | gemini-2.5-flash | image/link+text | json | yes | yes | no | no_if_failed | yes | 9000 | 1200 | 1 | 0 | 0.005700 | 0.006840 | Link mode replaces image analysis with parser/extractor. |
| similar_search | 2 | search_query_builder | marketplace_agent | gemini | gemini-2.5-flash | json | json | yes | yes | no | included | yes | 5000 | 1000 | 0 | 0 | 0.004000 | 0.004800 | Builds explicit legal marketplace query. |
| similar_search | 3 | marketplace_connector_cost | marketplace_connector | external_api | configured_connector | json | json | yes | yes | no | yes_if_success | no | 0 | 0 | 0 | 0 | 0.000000 | 0.000000 | Configurable placeholder: external_api_cost_usd, parser/proxy/search cost, and connector fees must be configured per approved marketplace. |
| similar_search | 4 | no_result_search_cost | marketplace_connector | external_api | configured_connector | json | json | no | yes | no | no_if_no_value | yes | 0 | 0 | 0 | 0 | 0.000000 | 0.000000 | Configurable no-result search cost; failed/no-result provider cost can be internal/free to user. |
| similar_search | 5 | pricing_explanation | pricing_agent | gemini | gemini-2.5-flash | json | json | optional | yes | no | included | no | 6000 | 1500 | 0 | 0 | 0.005550 | 0.006660 | Explains cheaper/similar trade-offs. |
| outfit_recommendation | 1 | garment_identity_analysis | garment_identity_agent | gemini | gemini-2.5-flash | image+text | json | yes | yes | no | no_if_failed | yes | 10000 | 1200 | 1 | 0 | 0.006000 | 0.007200 | Base garment understanding. |
| outfit_recommendation | 2 | user_profile_backend_service | user_profile_backend_service | backend | postgres | json | json | yes | no | no | included | yes | 0 | 0 | 0 | 0 | 0.000000 | 0.000000 | Backend-owned profile read, no LLM agent invocation. |
| outfit_recommendation | 3 | styling | fashion_stylist_agent | gemini | gemini-2.5-flash | json | json | yes | yes | no | yes_if_success | yes | 8000 | 2500 | 0 | 0 | 0.008650 | 0.010380 | Generates practical outfit options. |
| outfit_recommendation | 4 | trends | trend_agent | gemini | gemini-2.5-flash | json | json | optional | yes | no | yes_if_requested | no | 6000 | 1500 | 0 | 0 | 0.005550 | 0.006660 | Optional trend-aware recommendation. |
| outfit_recommendation | 5 | marketplace_items | marketplace_agent | gemini | gemini-2.5-flash | json | json | optional | yes | no | yes_if_requested | no | 6000 | 1500 | 0 | 0 | 0.005550 | 0.006660 | Optional real product suggestions. |
| pricing | 1 | garment_analysis_reuse_or_create | garment_identity_agent | gemini | gemini-2.5-flash | image/json | json | optional | yes | no | no_if_failed | yes | 9000 | 1200 | 1 | 0 | 0.005700 | 0.006840 | Reuse saved analysis when available. |
| pricing | 2 | competitor_search | marketplace_agent | gemini | gemini-2.5-flash | json | json | optional | yes | no | included | no | 6000 | 1500 | 0 | 0 | 0.005550 | 0.006660 | Requires explicit approved data source. |
| pricing | 3 | backend_price_calculation | pricing_backend | backend | postgres | json | json | yes | no | no | included | yes | 0 | 0 | 0 | 0 | 0.000000 | 0.000000 | Deterministic backend calculation. |
| pricing | 4 | pricing_explanation | pricing_agent | gemini | gemini-2.5-flash | json | json | yes | yes | no | yes_if_success | yes | 7000 | 1800 | 0 | 0 | 0.006600 | 0.007920 | Explains range and positioning. |
| content_package | 1 | saved_product_card_read | product_card_repository | backend | postgres | json | json | yes | no | no | included | yes | 0 | 0 | 0 | 0 | 0.000000 | 0.000000 | Reuses saved card and garment analysis. |
| content_package | 2 | business_profile_backend_service | business_profile_backend_service | backend | postgres | json | json | yes | no | no | included | yes | 0 | 0 | 0 | 0 | 0.000000 | 0.000000 | Backend-owned business profile read, no LLM agent invocation. |
| content_package | 3 | channel_copy | product_card_agent | gemini | gemini-2.5-flash | json | json | yes | yes | no | yes_if_success | yes | 10000 | 3000 | 0 | 0 | 0.010500 | 0.012600 | Creates channel-specific copy. |
| content_package | 4 | stylist_tone | fashion_stylist_agent | gemini | gemini-2.5-flash | json | json | optional | yes | no | included | no | 6000 | 1500 | 0 | 0 | 0.005550 | 0.006660 | Optional style/tone support. |
| content_package | 5 | visual_generation | content_image_generation | google_vertex | virtual-try-on-estimate | image+json | image | optional | yes | yes | yes_if_requested | yes | 0 | 0 | 1 | 1 | 0.040000 | 0.048000 | Per generated visual. |
| content_package | 6 | visual_quality | quality_verifier_agent | gemini | gemini-2.5-flash | image+json | json | optional | yes | no | included | yes | 10000 | 1200 | 1 | 0 | 0.006000 | 0.007200 | Per generated visual. |
| content_package | 7 | export_zip | export_service | backend | object_storage | json | artifact | optional | yes | no | yes_if_requested | no | 0 | 0 | 0 | 0 | 0.000000 | 0.001000 | Internal storage/export estimate. |
