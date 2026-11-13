# Price-Match Comparison Report

> Complete one copy per price-match run. Nothing changes until the owner
> approves the exact change list below. A changed row needs fresh approval.
> Fill in every [bracketed] field — never leave a decision blank and never
> guess one.

## Run

- **Date run:** [date]
- **Own store:** [store URL] — currency: [currency]
- **Competitor store:** [competitor URL]
- **Own catalog fetched:** [date/time] — [N] products
- **Competitor catalog fetched:** [date/time] — [N] products
- **Mode (circle one):** Only-lower (default) / Exact-match (owner chose it explicitly)
- **Compare-at rule:** [exact rule, e.g. new compare-at = 2× new price]
- **Explicitly NOT wanted:** [e.g. no raising any price, no touching named products]

## Counts

- **Matched:** [N] own-store singles matched against the competitor
- **Unmatched own singles:** [N] — listed below with reasons
- **Unmatched competitor products:** [N]
- **Lower (own dearer than competitor):** [N] — total cut: [amount + currency]
- **Raise (own cheaper than competitor):** [N] — total rise: [amount + currency]
- **Same price:** [N]
- **Bundles excluded from matching:** [N]
- **Competitor duplicates flagged (cheaper listing used):** [N] — [which products]

## Change list — approval gate (mandatory)

- **Change-list file (exact path):** [path to the CSV]
- **Rows in the change list:** [N]
- **Total cut:** [amount + currency] — **Total rise:** [amount + currency, or "none — only-lower mode"]
- **Heroes (best-known products, spot-checked against the competitor's live site):**

| Product | Own price now | New price | New compare-at |
|---|---|---|---|
| [hero 1] | | | |
| [hero 2] | | | |
| [hero 3] | | | |

- **Owner approved the exact change list:** [ ] Yes — name / date:

Do NOT apply if the approval box above is unticked. If any row changed after approval, get fresh approval first.

## Unmatched own-store products (left untouched)

| Product | Size | Reason |
|---|---|---|
| [product] | [size] | [no competitor product / same product at a different size] |

## Applied

- **Applied by:** [name] — **Date/time:** [date/time]
- **Route:** Bulk editor / Admin API
- **Rows applied:** [N] — **Rows failed:** [N] — [which rows, if any]

## Verification (0 mismatches required)

- **Fresh products.json fetched:** [date/time]
- **Changed products verified:** [N]/[N] at the new values
- **Unchanged products verified unchanged:** [N]/[N]
- **Mismatches:** 0 — **Verifier output:** [paste the RESULT line from scripts/verify_prices.py]
- **Verification passed:** [ ] Yes — date:

## Result

- **Store is now equal to or cheaper than the competitor on:** [N]/[N] matched products
- **Still pending (if anything):** [e.g. a failed row, a product the owner must decide on]
- **Files kept together for the next run:** [comparison file, change list, fresh products.json]
