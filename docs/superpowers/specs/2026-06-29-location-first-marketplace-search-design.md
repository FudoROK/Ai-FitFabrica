# Location-First Marketplace Search Foundation Design

## Goal

Build the backend foundation for "upload garment -> search similar/cheaper products" with location-first ranking and approved data-source contracts.

## Product Decision

Search must prioritize the customer's location:

```text
same city
-> same country
-> delivery available to customer city
-> lower price / budget fit
-> visual/text similarity
-> source trust
```

The first searchable source is the approved local B2B catalog. External marketplaces, Instagram, partner feeds, and connected seller stores are future connectors and must use approved contracts. Hidden scraping is not allowed.

## User Flow

1. User uploads a garment photo or provides a product link.
2. Backend creates a search job.
3. Garment Identity Agent analyzes garment type, color, cut, and visible details.
4. Backend converts the analysis into a structured search profile.
5. Backend queries approved connector sources.
6. Backend ranks results by location-first policy.
7. Frontend shows similar and cheaper products with city/country/delivery explanation.

## Scope

In scope:

- Connector source contract.
- Normalized offer contract.
- Location-first ranking policy.
- Business catalog search projection mapping.
- Similar Search domain extension for user country/city.
- Tests and documentation.

Out of scope:

- Kaspi/Wildberries live API integration.
- Instagram Graph API integration.
- Seller connected-store publishing.
- Hidden scraping.
- Image embedding generation for catalog products.
- Frontend redesign.

## Architecture

```text
Frontend upload/search action
-> FastAPI Similar Search route
-> SimilarSearchWorkflowService
-> Garment/query profile
-> connector ports
-> approved local catalog projection
-> location-first ranking policy
-> typed response
```

Agents do not call marketplaces. Marketplace Agent can later return a structured search strategy, but backend owns connector calls, ranking, cost accounting, and persistence.

## Connector Source Types

Allowed source types:

- `local_catalog`
- `partner_feed`
- `official_api`
- `seller_connected_store`
- `admin_verified_link`
- `instagram_business`

Disallowed:

- hidden scraping;
- bypassing marketplace rules;
- unapproved public scraping;
- browser automation against marketplace pages.

## Normalized Offer Fields

Every connector result must normalize into:

- source type;
- source id;
- product id;
- title;
- category;
- price amount;
- currency;
- country code;
- city;
- delivery regions;
- product URL;
- availability;
- source trust score;
- freshness timestamp optional.

## Error Handling

Connector failures must be isolated:

- one failed connector must not fail the whole search;
- no-result search is a valid outcome and must be cost-accounted later;
- backend returns structured errors only for complete workflow failure.

## Acceptance Criteria

- Similar Search request supports `user_country_code` and `user_city`.
- Ranking explains location fit.
- Local B2B approved product projection can map into normalized connector offers.
- Tests prove same-city results outrank same-country and cheaper remote results.
- No external scraping exists.
