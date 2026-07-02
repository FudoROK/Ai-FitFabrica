# Credits Pricing Table v1

Date: 2026-06-16

Baseline exchange: `1 credit = 50 KZT`.

Planning assumptions:

- `1 USD = 500 KZT`.
- Conservative multiplier: `5x`.
- Balanced multiplier: `3x`.
- Aggressive multiplier: `2x`.
- Recommended public starting point: balanced, then adjust after real production usage data.

| product_action | workflow_type | direct_cost_usd_min | direct_cost_usd_avg | direct_cost_usd_max | internal_cost_kzt_avg | recommended_credits_conservative | recommended_credits_balanced | recommended_credits_aggressive | user_price_kzt | expected_margin_percent | notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| B2C Try-On Basic | try_on | 0.06 | 0.09 | 0.14 | 45 | 5 | 3 | 2 | 150 | 70.00 | Includes analysis, generation, quality verification. |
| B2C Try-On + Stylist Advice | try_on | 0.07 | 0.10 | 0.16 | 50 | 5 | 3 | 2 | 150 | 66.67 | Adds Fashion Stylist Agent. |
| B2C Extra Try-On Variant | try_on | 0.04 | 0.06 | 0.10 | 30 | 3 | 2 | 2 | 100 | 70.00 | User-requested variant is paid. |
| B2B Product Card Text Only | product_card | 0.02 | 0.04 | 0.07 | 20 | 2 | 2 | 1 | 100 | 80.00 | Garment analysis plus Product Card Agent text/json output. |
| B2B Product Card + 1 Model Photo | product_card | 0.05 | 0.08 | 0.13 | 40 | 4 | 3 | 2 | 150 | 73.33 | Adds one model-photo generation estimate, without separate quality gate. |
| B2B Product Card + Model Photo + Quality Verification | product_card | 0.06 | 0.09 | 0.15 | 45 | 5 | 3 | 2 | 150 | 70.00 | Adds one generated visual and Quality Verifier. |
| B2B Product Card + Content Package | content_package | 0.08 | 0.13 | 0.22 | 65 | 7 | 4 | 3 | 200 | 67.50 | Product Card plus channel copy/export package. |
| Similar Product Search | similar_search | 0.01 | 0.03 | 0.06 | 15 | 2 | 1 | 1 | 50 | 70.00 | Marketplace connector fees configured separately. |
| Cheaper Product Search | similar_search | 0.01 | 0.03 | 0.06 | 15 | 2 | 1 | 1 | 50 | 70.00 | Same baseline as similar search. |
| Outfit Recommendation | outfit_recommendation | 0.02 | 0.05 | 0.09 | 25 | 3 | 2 | 1 | 100 | 75.00 | Marketplace/trend add-ons increase cost. |
| Pricing Report | pricing | 0.01 | 0.03 | 0.06 | 15 | 2 | 1 | 1 | 50 | 70.00 | Reuse saved analysis when possible. |
| Content Package Text Only | content_package | 0.03 | 0.05 | 0.09 | 25 | 3 | 2 | 1 | 100 | 75.00 | Channel copy/export without generated images. |
| Content Package + 1 Generated Image | content_package | 0.07 | 0.10 | 0.17 | 50 | 5 | 3 | 2 | 150 | 66.67 | Text package plus one generated visual and quality gate. |
| Content Package + 3 Generated Images | content_package | 0.15 | 0.22 | 0.35 | 110 | 11 | 7 | 5 | 350 | 68.57 | Three generated visuals; repair risk reserve needed. |
| Content Package + 5 Generated Images | content_package | 0.23 | 0.34 | 0.55 | 170 | 17 | 11 | 7 | 550 | 69.09 | Five generated visuals; should be sold as larger B2B package. |

The table is intentionally conservative and must be recalibrated after real production usage reports show actual provider costs, retries, repairs, and conversion rates.

## Recalibration Report Requirement

After 20-50 real staging/prod runs, prepare a recalibration report with:

- actual avg Try-On cost;
- actual avg Product Card cost;
- repair rate;
- retry rate;
- failed free job cost;
- real margin by workflow.

The recalibration report should update recommended credits only after comparing real provider costs, failed free jobs, retry/repair rate, and successful workflow margin. Live billing remains unchanged until that recalibration is reviewed separately.
