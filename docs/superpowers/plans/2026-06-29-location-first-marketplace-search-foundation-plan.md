# Location-First Marketplace Search Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add provider-safe marketplace connector contracts and location-first ranking foundation for Similar Search.

**Architecture:** Keep frontend thin and backend-owned. Similar Search receives user location, hydrates approved offers through connector/catalog ports, then ranks by city, country, delivery, price, similarity, and source trust.

**Tech Stack:** FastAPI, Pydantic, Python use-cases/domain, pytest, existing B2B catalog projection.

---

## Files

- Create: `src/domain/marketplace_search.py`
- Create: `src/use_cases/similar_search/location_ranking.py`
- Modify: `src/domain/similar_search.py`
- Modify: `src/use_cases/similar_search/ranking.py`
- Modify: `src/use_cases/business_catalog/search_projection.py`
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`
- Test: `tests/test_marketplace_search_contracts.py`
- Test: `tests/test_similar_search_location_ranking.py`
- Test: `tests/test_business_catalog_search_projection.py`

## Task 1: Connector Contracts

- [x] Create marketplace source and normalized offer contracts.
- [x] Test allowed source types and anti-scraping policy.
- [x] Verify strict Pydantic validation.

## Task 2: Similar Search Location Fields

- [x] Add `user_country_code` and `user_city` to `SimilarSearchRequest`.
- [x] Add geo/source fields to offer/result models.
- [x] Keep backwards compatibility for existing tests.

## Task 3: Location-First Ranking

- [x] Add location fit scoring: same city, same country, delivery to city.
- [x] Update ranking to prioritize location before price and similarity.
- [x] Add explanations for city/country/delivery matches.

## Task 4: Local Catalog Projection Mapping

- [x] Extend B2B catalog search projection to expose normalized source metadata.
- [x] Keep projection limited to `active` + `approved` products with offers.
- [x] Add tests for local catalog source type, geo, delivery, and trust score.

## Task 5: Verification And Docs

- [x] Run targeted tests for marketplace contracts, ranking, B2B projection, similar search.
- [x] Run architecture guardrail and compileall.
- [x] Update action log with exact verification results.
