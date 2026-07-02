# Credits Policy v1

Date: 2026-06-16

Internal currency name: FitFabrica Credits, shown to users as `credits`.

This policy separates user-facing credits from provider tokens. Credits are product billing units. LLM tokens are provider usage units. They must not be mixed in UI, ledger, or reports.

## Do Not Charge Credits

Credits must not be charged when the workflow fails before user-visible value is produced:

- Human Identity blocked unsuitable photo
- Garment Identity failed before generation
- provider/system error
- contract validation failed
- backend policy rejected input
- Try-On Instruction failed before image generation
- generation failed because of provider/system error
- Quality Verifier rejected a result before user delivery

## Charge Credits

Credits may be charged when the backend successfully produces the requested value:

- successful Try-On
- successful Product Card
- successful Similar Search
- successful Outfit Recommendation
- successful Pricing Report
- successful Content Package
- user-requested extra variant
- user-requested regeneration
- user-requested expanded marketplace search
- user-requested generated visual asset

## Free To User

The platform absorbs these costs:

- repair caused by our quality failure
- retry caused by provider/system failure
- repeated Quality Verifier after our repair
- failed workflow caused by contract validation or backend policy rejection

## Paid By User

These are new paid actions because they create new requested value:

- additional variant requested by the user
- new generation after input change
- new similar/cheaper search
- expanded content package
- extra generated image beyond the selected package

## Billing Authority

The backend is the only authority for credits. Frontend may display estimated cost, final charged amount, and refund/free-repair status, but must not calculate or modify credits.
