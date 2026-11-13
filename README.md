# Shopify Price-Match Skill

A Claude skill for competitor price-matching on a Shopify store, built from Asjad's real price-match work on Fragrance Empire. Claude handles all the work end to end — fetch both stores' prices, match products, build the change list, verify the changes live — with the owner involved only for two decisions (which mode, and the approval gate) and for applying the changes in Shopify Admin. By default the skill only ever lowers prices, never raises them.

## What it does

Takes a store from "are we pricier than the competitor?" to verified new prices in one repeatable workflow:

1. **Brief** — the store, the competitor, the currency, the mode (only-lower by default), and the compare-at rule. No matching before the brief is confirmed.
2. **Fetch** — both stores' public `products.json` (prices only — never the competitor's images or text).
3. **Match** — canonical product keys (sorted tokens, unified brand aliases), size matched separately, competitor duplicates resolved to the cheaper listing.
4. **Compare** — every matched product sorted into lower / raise / same, plus the unmatched list with the reason for each.
5. **Change list** — the exact rows to apply, in the bulk-editor CSV format. Only-lower by default; exact-match is an option the owner must choose.
6. **Approval gate** — nothing changes until the owner approves the exact change list.
7. **Apply** — via Shopify bulk editor (or Admin API), exactly the approved rows.
8. **Verify live** — re-fetch the store's `products.json` and check every changed product, plus check the unchanged ones stayed unchanged. Zero mismatches required before reporting done.
9. **Report** — what changed, what stayed, what did not match, and the total saving.

## Who does what — Claude handles all the work end to end

Claude runs every step — brief, fetching, matching, comparing, the change list, the verification script, and the report. The owner is involved only at three points: (1) the brief decisions (which competitor, which mode, the compare-at rule); (2) the approval gate for the exact change list; and (3) applying the changes in Shopify Admin (browser, with the owner's sign-in) or approving the Admin API route. Everything else is Claude's work — do not hand it back to the owner as homework.

## The live example — Fragrance Empire vs Fragrance Pro Max, 10 Nov 2026

- **Store:** Fragrance Empire — https://fragranceempire.my (Shopify, 155 products = 142 singles + 13 bundles, 18 brands, MYR, Malaysia)
- **Competitor:** Fragrance Pro Max — https://fragrancepromax.com (Shopify store, flat 50% off, no code)
- **Matched:** 111 Fragrance Empire singles matched against the competitor; 31 singles unmatched (FE-only products + 2 size mismatches); 0 competitor products unmatched
- **Owner's choice:** ONLY-LOWER — 70 products lowered, 0 raised, every new compare-at price exactly 2× the new price
- **Total of the 70 cuts:** RM 1,940.80
- **Verified live** via the store's `products.json`: 70/70 at the new values, 0 mismatches; the 41 already-cheaper products left unchanged
- **Result:** Fragrance Empire is now equal to or cheaper than Fragrance Pro Max on all 111 matched products

Heroes after matching:

| Product | New price | New compare-at |
|---|---|---|
| Dior Sauvage EDP 100 ML | RM 120.00 | RM 240.00 |
| Paco Rabanne 1 Million EDT 100 ML | RM 105.00 | RM 210.00 |
| Versace Eros EDP 100 ML | RM 115.00 | RM 230.00 |
| Black Opium Glitter EDP 100 ML | RM 110.00 | RM 220.00 |

- **Built by:** Asjad Farooq, Shopify Store Designer — Fiverr gig https://www.fiverr.com/s/L34yBpA

## Files

```
shopify-price-match/
├── README.md                                  # this file
└── shopify-price-match/
    ├── SKILL.md                               # the Claude skill — the workflow itself
    ├── scripts/
    │   ├── match_prices.py                    # matcher: products.json in, comparison + change list out
    │   └── verify_prices.py                   # verifier: change list + fresh products.json in, PASS/FAIL out
    └── templates/
        ├── change-list.csv                    # change-list CSV template (bulk-editor format)
        └── comparison-report.md               # comparison report template + approval gate
```

## Setup

### 1. The two data sources

Both inputs are the stores' public `products.json` files — no login, no API key, no credentials:

- Own store: `https://<own-store>/products.json` (paginate with `?page=N&limit=250` if the catalog is over 250 products)
- Competitor store: `https://<competitor-store>/products.json` (same pagination rule)

Save both files locally before running the matcher. Prices are a snapshot — re-fetch both files on the day the changes are applied, because the competitor's prices may have moved since the last run.

### 2. Apply route (one of these)

**Route A — Shopify bulk editor (used in the live example).** Open the change-list CSV, paste the rows into Admin > Products (bulk editor), save, and check the confirmation. The owner applies it in the browser with their own sign-in, or approves a browser task to do it.

**Route B — Admin API.** Only with an access token the owner creates in a custom app. Never paste credentials into the skill files, into chat, or into the repo — tokens live only in the owner's secure storage.

Do not use any other apply route.

### 3. Use in Claude

Copy the `shopify-price-match/` folder into a Claude skills directory (for example a Claude Code skills folder, or a repo Claude is pointed at), or keep this whole repo and point Claude at `shopify-price-match/SKILL.md`. Then ask Claude to run the workflow, for example: "Match my store's prices against <competitor> using the shopify-price-match skill."

## Honest limits — read before using

- **Only-lower is the default, and it is the safe default.** Exact-match (which raises some prices) is available only when the owner explicitly chooses it. Never raise a price on Claude's own initiative.
- **A compare-at price must be a price the product was actually sold at, or the owner's recorded pricing model.** Never invent a compare-at price. In the live example the owner's rule was compare-at = 2× the new price; that rule was the owner's decision, and the misleading-price risk of a "was" price that was never charged was flagged to the owner first.
- **Never guess on size-ambiguous matches.** If the same product exists at a different size, or the size cannot be read, the product stays unmatched and is listed for the owner. Do not match it anyway.
- **Prices only from the competitor.** Never copy the competitor's images, product text, descriptions or branding. The competitor is a price reference only.
- **No credentials in the skill.** No API keys, passwords or access tokens are stored in these files. Admin access happens on the owner's own device.
- **Approval gate is mandatory.** No price changes until the owner approves the exact change list. A changed row needs fresh approval.
- **Verification is part of the job, not an extra.** A price-match is not done until the live store has been re-checked product by product. Report the verification counts, never just the change list.

## How to run one price-match

1. Fill in the brief (Step 1) and get the owner to confirm it — store, competitor, mode, compare-at rule.
2. Fetch both stores' `products.json` (fresh, same day) and save them locally.
3. Run `scripts/match_prices.py` and read the summary: matched, unmatched, lower / raise / same counts.
4. Review the unmatched list with the owner — never force a match.
5. Build the change list from the script output (only-lower, unless the owner chose exact-match).
6. Fill in `templates/comparison-report.md` and get the owner's approval for the exact change list.
7. Apply the approved rows via Route A or Route B.
8. Re-fetch the store's `products.json` and run `scripts/verify_prices.py` — 0 mismatches required.
9. Return the completed report to the owner: what changed, what stayed, what did not match.
