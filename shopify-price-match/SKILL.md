---
name: shopify-price-match
description: Competitor price-matching for a Shopify store — Claude fetches the store's and the competitor's public products.json, matches products by canonical key (sorted tokens, unified brand aliases) with size matched separately, and produces a safe owner-approved change list (only-lower by default, never raising prices without the owner's explicit choice), then verifies every change live via products.json before reporting done. Modeled on the live Fragrance Empire vs Fragrance Pro Max price match of 10 Nov 2026 (111 matched, 70 lowered, 0 raised, 70/70 verified live). Use when the user asks to compare store prices against a competitor, match prices, lower prices to beat a competitor, or check whether the store is cheaper than a competitor.
---

# Shopify Price-Match

## When to use

Use this skill when the user asks to compare their Shopify store's prices against a competitor's prices, match a competitor's prices, lower prices to be cheaper than a competitor, or check whether the store is already cheaper than a competitor.

Do not use it for bundles (bundles are priced as their own products with their own rules — match singles only), for non-Shopify stores unless both sides expose a `products.json` feed, or for copying anything other than prices from the competitor. If the user wants a sale, a discount code or a repricing scheme (for example raise-then-discount), that is a separate job — this skill only compares and matches prices.

## Who does what — Claude handles all the work end to end

Claude runs every step of the workflow below — brief, fetching, matching, comparing, the change list, verification and the report. The owner is involved only at three points:

1. **Brief decisions** — which competitor, which mode (only-lower or exact-match), and the compare-at rule. Claude drafts the brief; the owner supplies the facts and confirms them.
2. **Approval gate** — the owner approves the exact change list before anything is applied (see Step 6). Nothing changes without that approval.
3. **Applying the changes** — the owner applies them in Shopify Admin (browser, with the owner's sign-in) or approves the Admin API route with a token the owner creates. Claude never handles the owner's password or token.

Everything else — fetching, matching, comparing, the change list, verification, the report — is Claude's work. Do not hand any of it back to the owner as homework.

## Store facts — the live reference case (do not invent others)

Fragrance Empire vs Fragrance Pro Max, run on 10 Nov 2026. Use these real numbers as the reference example.

- **Store:** Fragrance Empire — https://fragranceempire.my. Shopify, 155 products = 142 single products + 13 bundles, 18 brands, currency MYR, market Malaysia.
- **Competitor:** Fragrance Pro Max — https://fragrancepromax.com. Shopify store, flat 50% off, no discount code.
- **Scope:** singles only. The 13 bundles were excluded from matching and left as-is.
- **Matched:** 111 Fragrance Empire singles matched. 31 singles unmatched (FE-only products + 2 size mismatches). 0 competitor products unmatched.
- **Owner's choice:** ONLY-LOWER. 70 products lowered, 0 raised. Every new compare-at price exactly 2× the new price. Total of the 70 cuts: RM 1,940.80.
- **Applied:** 10 Nov 2026, Shopify bulk editor, exactly the 70 approved rows, 0 failed.
- **Verified live** via the store's `products.json`: 70/70 at the new values, 0 mismatches; the 41 already-cheaper products verified unchanged.
- **Result:** Fragrance Empire is equal to or cheaper than Fragrance Pro Max on all 111 matched products.
- **Heroes after matching:** Dior Sauvage EDP 100 ML RM 120.00 / 240.00; Paco Rabanne 1 Million EDT 100 ML RM 105.00 / 210.00; Versace Eros EDP 100 ML RM 115.00 / 230.00; Black Opium Glitter EDP 100 ML RM 110.00 / 220.00.
- **Competitor duplicates:** Narciso Rodriguez For Her Fleur Musc EDP, For Her EDP and For Her EDT each appear on the competitor at RM 115 AND RM 99 — the matcher used the cheaper RM 99 as the reference price and flagged the duplicates.
- **Seller services (Fiverr gig https://www.fiverr.com/s/L34yBpA):** Basic $80 — 10 products, 5 pages, 3 days; Standard $180 — 30 products, 8 pages, 5 days; Premium $350 — 50 products, 10 pages, 7 days. Unlimited revisions on all three packages.

## Hard limits — state them honestly, do not work around them

- **Only-lower is the default. Never raise a price without the owner's explicit choice.** Exact-match (which raises the products that are currently cheaper than the competitor) is available only when the owner explicitly chooses it, after seeing both lists and the totals. Never present exact-match as the default, and never raise a price silently inside a change list.
- **Never set a compare-at price the product never sold at, unless it is the owner's recorded pricing model.** A compare-at price is the price before the current offer. Never invent one. In the reference case the owner's rule was compare-at = 2× the new price; that rule was the owner's decision, and the misleading-price risk of a "was" price that was never charged was flagged to the owner before applying it. If the owner has no compare-at rule, ask — do not fill one in.
- **Never guess on size-ambiguous matches.** A match requires the same product AND the same size. If the size cannot be read from a title, or the same product exists at a different size, the product stays unmatched and is listed for the owner with the reason. Do not match it anyway, and do not attach a competitor's price to the wrong size.
- **Prices only from the competitor.** Never copy the competitor's images, product text, descriptions, branding or reviews. The competitor is a price reference only.
- **Prices are a snapshot.** Re-fetch both stores' `products.json` on the day the changes are applied. If the competitor's prices moved since the match was run, re-run the match before applying — do not apply a stale change list.
- **No credentials in the skill.** Never put an API key, password or access token in a skill file, in chat, or in a repo. Admin access happens on the owner's own device.
- **Approval gate is mandatory.** No price changes until the owner approves the exact change list. A changed row needs fresh approval.
- **Verification is part of the job.** A price-match is not done until the live store has been re-checked product by product and the verification counts are reported. Never report "done" from the change list alone.

## Workflow

### Step 1 — Brief (decisions first, no matching before this)

Collect and write down, in `templates/comparison-report.md`:

1. Own store URL and currency.
2. Competitor store URL (must be a Shopify store exposing `products.json` — check this first; if it does not, stop and tell the owner).
3. Scope: singles only (bundles excluded). If the owner wants bundles matched too, agree the bundle rule separately before starting.
4. Mode: **only-lower (default)** or **exact-match (owner must choose it explicitly)**. Show the owner what each mode means: only-lower changes only the products that are currently dearer than the competitor; exact-match also raises the products that are currently cheaper.
5. Compare-at rule: the exact rule for the new compare-at price (in the reference case: exactly 2× the new price). If the owner has no rule, ask — do not invent one.
6. Anything the owner explicitly does NOT want (for example: no raising any price, no touching named products, no change to bundles).

Do not start Step 2 until the brief is filled in and the owner has confirmed it.

### Step 2 — Fetch both stores' products.json

1. Fetch the own store's catalog: `https://<own-store>/products.json`. Paginate with `?page=N&limit=250` until no more products come back. Save the full file locally.
2. Fetch the competitor's catalog the same way and save it locally.
3. Record the fetch date and time in the report, and the product count on each side. If either fetch returns an error or an empty list, stop — do not match from a partial catalog.
4. Use the saved files for the whole run. Do not mix a fresh fetch with an old one halfway through.

### Step 3 — Match (run the script)

Run `scripts/match_prices.py` with the two saved files. It does:

1. **Canonical keys.** Each product title is reduced to a canonical key: the title head (before the " – " separator), folded to lowercase with accents stripped, brand aliases unified (for example "Paco Rabanne" → "rabanne", "Giorgio Armani" → "armani", "Yves Saint Laurent" / "Saint Laurent" → "ysl", "eau de parfum" → "edp", "eau de toilette" → "edt"), the word "by" dropped, duplicate tokens removed, and the remaining tokens SORTED alphabetically. Sorting absorbs brand-position differences ("Lancôme Trésor" vs "Trésor by Lancôme") while keeping the brand in the key, so different brands' same-named lines (Polo Black vs Dunhill Black) never collide.
2. **Size matched separately.** The size is read from the title (`100 ML`, `200ml`) and matched as its own field. A match requires the same key AND the same size. If no size is stated, the script defaults to 100 ml and flags the assumption — do not trust a defaulted size for a product the owner cares about; check it.
3. **Competitor duplicates resolved to the cheaper listing.** If the competitor lists the same product twice at different prices, the cheaper price is the reference and the duplicate is flagged in the output. In the reference case the Narciso Rodriguez For Her lines appeared at RM 115 and RM 99 — the matcher used RM 99.
4. **Bundles excluded.** Products whose title contains "Bundle" are left out of matching on the own-store side and counted separately.
5. **Outputs.** A comparison file (every matched product with both prices and the delta), a change-list file (only the rows to apply, in the mode chosen), and an unmatched file (every unmatched own-store product with the reason: no competitor product, or same product at a different size).

Read the printed summary before going further: matched count, unmatched count, lower / raise / same counts, total down, total up, biggest drops, biggest rises, duplicates flagged. If the matched count looks wrong (for example far fewer matches than the catalog overlap suggests), stop and check the keys — do not push a bad match through.

### Step 4 — Review the unmatched list (never force a match)

1. Read every unmatched own-store product and its reason. The two reasons are: "no competitor product" (the store-only product — leave it alone) and "same product at a different size" (the competitor sells it in another size — leave it alone unless the owner says otherwise).
2. Put the unmatched list in the report, in full, so the owner sees exactly what was not touched and why.
3. Never force a match to make the numbers look better. An unmatched product is a correct outcome, not a failure — in the reference case 31 products were correctly unmatched.

### Step 5 — Build the change list

1. Take the change-list file from the script output. In only-lower mode it contains only the products where the competitor is cheaper; in exact-match mode it contains every matched product whose price differs.
2. Check every row by hand against the comparison file: new price = competitor price, new compare-at = the brief's rule applied to the new price, delta = new price − current price (negative for a cut). Every row in only-lower mode must have a negative delta — if any row has a positive delta, stop: the mode or the file is wrong.
3. Write the change list into `templates/change-list.csv` format: Product, Handle, New Price, New Compare-at, Own Price Now, Delta. Keep the currency label from the brief.
4. Total the cuts (and the rises, in exact-match mode) and write the totals in the report. In the reference case the 70 cuts totalled RM 1,940.80.
5. Spot-check the heroes (the best-known products) against the competitor's live site before approval — if a hero price is wrong, the whole list is suspect.

### Step 6 — Approval gate (mandatory)

Fill in `templates/comparison-report.md` and show the owner:

- The counts (matched / unmatched / changed / unchanged).
- The full change list, or the heroes plus the totals if the list is long — with the full CSV attached, never a summary alone.
- The unmatched list and the reasons.
- The totals (total cut, and total rise if exact-match mode).

Then stop and get the owner's approval for the exact change list. Launch nothing until it is approved. If the owner changes even one row, that is a new change list and needs fresh approval.

### Step 7 — Apply (exactly the approved rows)

Apply via one of the two routes in the README:

- **Route A — Shopify bulk editor.** Paste the approved rows into Admin > Products (bulk editor), save, and record the confirmation. Apply exactly the approved rows — no extra products, no edited prices.
- **Route B — Admin API.** Only with an access token the owner creates. Apply exactly the approved rows.

Record who applied it, when, and how many rows. If any row fails to apply, stop and tell the owner — do not silently skip it and report the rest as done.

### Step 8 — Verify live (0 mismatches required)

1. Re-fetch the own store's `products.json` fresh — do not verify against the file from Step 2.
2. Run `scripts/verify_prices.py` with the approved change-list CSV and the fresh `products.json`. It checks every changed product's live price and compare-at price against the change list, row by row.
3. Also check the unchanged products stayed unchanged: pass the pre-change snapshot to the verifier (or compare the fresh file against it) and report any unexpected change.
4. Required result before reporting done: every changed product at its new value, 0 mismatches, and the unchanged products verified unchanged. In the reference case: 70/70 at the new values, 0 mismatches, 41/41 already-cheaper products unchanged.
5. If any product does not match, do not report the job as done — fix it (re-apply that row) and re-verify until the counts are clean.

### Step 9 — Report

Return the completed `templates/comparison-report.md` to the owner:

- What changed (count, total cut/rise, heroes).
- What stayed unchanged (count, and why).
- What did not match (count, with reasons).
- Verification counts (changed verified X/X, unchanged verified X/X, mismatches 0).
- Anything still pending (for example a failed row, a product the owner must decide on).

Keep the comparison file, the change list and the fresh `products.json` together so the next price-match starts from a known state.

## How to run one price-match

1. Fill in the brief (Step 1) and get the owner to confirm it — store, competitor, mode, compare-at rule.
2. Fetch both stores' `products.json` fresh and save them locally (Step 2).
3. Run `scripts/match_prices.py` and read the summary (Step 3).
4. Review the unmatched list — never force a match (Step 4).
5. Build the change list and check every row (Step 5).
6. Fill in `templates/comparison-report.md` and get the owner's approval for the exact change list (Step 6).
7. Apply exactly the approved rows (Step 7).
8. Re-fetch the store's `products.json` and run `scripts/verify_prices.py` — 0 mismatches required (Step 8).
9. Return the completed report to the owner (Step 9).
