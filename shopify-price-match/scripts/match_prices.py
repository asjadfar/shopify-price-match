#!/usr/bin/env python3
"""Match a Shopify store's prices against a competitor's prices.

Reads two Shopify products.json files (own store + competitor), matches
products by canonical key with size matched separately, and writes:
  <prefix>-comparison.csv  every matched product, both prices, delta
  <prefix>-change-list.csv  only the rows to apply (mode chosen)
  <prefix>-unmatched.csv   own-store products with no match + reason

Key = canonical title with brand tokens unified, concentration kept,
size extracted separately. Match requires same key AND same size.
Competitor duplicates are resolved to the cheaper listing and flagged.
Bundles (titles containing the bundle word) are excluded from matching.

Modes:
  only-lower  (default) change only products dearer than the competitor
  exact       change every matched product whose price differs

New compare-at price = new price x --compare-at-multiplier (the
reference case used 2.0, the owner's rule). The multiplier is the
owner's decision, not a default to apply blindly.

Usage:
  python3 match_prices.py own-products.json competitor-products.json \
      --mode only-lower --compare-at-multiplier 2.0 --currency RM \
      --out-prefix price-match

Inputs are Shopify products.json files ({"products": [...]}). Fetch them
fresh on the day the changes are applied; prices are a snapshot.
Only the first variant of each product is compared. Multi-variant
products need per-variant handling — this script does not do that.
"""
import argparse
import csv
import json
import re
import sys
import unicodedata


def fold(s):
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    return s.lower()


def size_of(title):
    """Size in ml from the title; (size, assumed). Defaults to 100 ml
    when no size is stated — the assumption is flagged, never trusted
    silently."""
    m = re.search(r"(\d+)\s*ml\b", title, re.I)
    return (int(m.group(1)), False) if m else (100, True)


def canon(title):
    """Canonical key: tokens of the title head (size removed), brand aliases
    unified, 'by' dropped, duplicate tokens removed, tokens SORTED
    alphabetically. Sorting absorbs brand-position differences
    ('Lancôme Trésor' vs 'Trésor by Lancôme') while keeping the brand in
    the key, so different brands' same-named lines (Polo Black vs
    Dunhill Black) never collide."""
    head = title.split(" \u2013 ")[0]
    h = fold(head)
    h = h.replace("&", " and ")
    h = re.sub(r"eau de parfum", "edp", h)
    h = re.sub(r"eau de toilette", "edt", h)
    h = re.sub(r"eau de cologne", "edc", h)
    h = re.sub(r"yves saint laurent", "ysl", h)
    h = re.sub(r"saint laurent", "ysl", h)
    h = re.sub(r"giorgio armani", "armani", h)
    h = re.sub(r"paco rabanne", "rabanne", h)
    h = re.sub(r"\b\d+\s*ml\b", " ", h)
    h = re.sub(r"([a-z])(\d)", r"\1 \2", h)
    h = re.sub(r"(\d)([a-z])", r"\1 \2", h)
    h = re.sub(r"[^a-z0-9 ]", " ", h)
    toks = sorted({t for t in h.split() if t != "by"})
    return " ".join(toks)


def load_products(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    products = data["products"] if isinstance(data, dict) else data
    return products


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("own_json", help="own store products.json")
    ap.add_argument("competitor_json", help="competitor products.json")
    ap.add_argument("--mode", choices=["only-lower", "exact"],
                    default="only-lower",
                    help="only-lower (default): change only products "
                         "dearer than the competitor")
    ap.add_argument("--compare-at-multiplier", type=float, default=2.0,
                    help="new compare-at = new price x this (owner's rule)")
    ap.add_argument("--currency", default="RM",
                    help="currency label for the CSV headers")
    ap.add_argument("--bundle-word", default="Bundle",
                    help="titles containing this word are excluded")
    ap.add_argument("--out-prefix", default="price-match",
                    help="output file prefix")
    args = ap.parse_args()

    own = load_products(args.own_json)
    comp = load_products(args.competitor_json)

    # Competitor by (key, size); flag duplicates and price disagreements.
    comp_by_ks = {}
    dup_notes = []
    for p in comp:
        k = canon(p["title"])
        sz, _ = size_of(p["title"])
        ks = (k, sz)
        pr = float(p["variants"][0]["price"])
        if ks in comp_by_ks:
            old = comp_by_ks[ks]
            old_pr = float(old["variants"][0]["price"])
            dup_notes.append((k, sz, old["title"], old_pr, p["title"], pr))
            # keep the cheaper listing as the reference price
            if pr < old_pr:
                comp_by_ks[ks] = p
        else:
            comp_by_ks[ks] = p

    print("Competitor entries:", len(comp),
          "| unique (key,size):", len(comp_by_ks))
    for k, sz, t0, pr0, t1, pr1 in dup_notes:
        print("  DUP competitor |", k, sz, "ml |", t0[:45], pr0,
              "||", t1[:45], pr1,
              ("  <-- PRICE DIFFERS" if pr0 != pr1 else ""))

    own_singles = [p for p in own if args.bundle_word not in p["title"]]
    own_bundles = [p for p in own if args.bundle_word in p["title"]]
    matched = []
    unmatched = []
    n_size_assumed = 0
    for p in own_singles:
        k = canon(p["title"])
        sz, assumed = size_of(p["title"])
        if assumed:
            n_size_assumed += 1
        c = comp_by_ks.get((k, sz))
        if c is not None:
            matched.append((p, c, k, sz, assumed))
        else:
            same_key = [kk for (kk, ss) in comp_by_ks if kk == k]
            why = ("same product, competitor size %s"
                   % [ss for (kk, ss) in comp_by_ks if kk == k]
                   if same_key else "no competitor product")
            unmatched.append((p, k, sz, why))
    matched_ks = {(k, sz) for _, _, k, sz, _ in matched}
    unmatched_comp = [(p, k, sz) for (k, sz), p in comp_by_ks.items()
                      if (k, sz) not in matched_ks]

    print("\nOwn singles:", len(own_singles),
          "| Own bundles (excluded):", len(own_bundles))
    print("MATCHED:", len(matched))
    print("UNMATCHED own singles:", len(unmatched))
    for p, k, sz, why in unmatched:
        print("  NO-MATCH |", p["title"].split(" \u2013 ")[0][:68],
              "|", sz, "ml |", why)
    print("UNMATCHED competitor:", len(unmatched_comp))
    for p, k, sz in unmatched_comp:
        print("  COMP-NO-MATCH |", p["title"][:68], "|", sz, "ml | key:", k)
    if n_size_assumed:
        print("NOTE: size assumed 100 ml for %d own-store product(s) — "
              "check these sizes by hand before applying."
              % n_size_assumed)

    rows = []
    n_down = n_up = n_same = 0
    total_down = total_up = 0.0
    for p, q, k, sz, assumed in matched:
        own_price = float(p["variants"][0]["price"])
        own_ca = p["variants"][0].get("compare_at_price")
        comp_price = float(q["variants"][0]["price"])
        comp_ca = q["variants"][0].get("compare_at_price")
        d = round(comp_price - own_price, 2)
        if d < 0:
            n_down += 1
            total_down += -d
        elif d > 0:
            n_up += 1
            total_up += d
        else:
            n_same += 1
        rows.append({
            "own_title": p["title"].split(" \u2013 ")[0],
            "own_id": p["id"],
            "own_handle": p["handle"],
            "own_price_now": own_price,
            "own_compare_now": own_ca,
            "comp_title": q["title"],
            "comp_price": comp_price,
            "comp_compare": comp_ca,
            "delta": d,
            "key": k,
            "size_ml": sz,
            "size_assumed": "yes" if assumed else "no",
        })
    print("\nMatched price changes (own now -> competitor):")
    print("  DOWN (own gets cheaper):", n_down,
          "total %.2f %s" % (total_down, args.currency))
    print("  UP   (own gets dearer):", n_up,
          "total %.2f %s" % (total_up, args.currency))
    print("  SAME:", n_same)
    rows.sort(key=lambda r: r["delta"])
    print("  -- biggest drops --")
    for r in rows[:8]:
        print("    %-52s %7.2f -> %7.2f (d %+6.2f)" % (
            r["own_title"][:52], r["own_price_now"],
            r["comp_price"], r["delta"]))
    print("  -- biggest rises --")
    for r in rows[-8:]:
        print("    %-52s %7.2f -> %7.2f (d %+6.2f)" % (
            r["own_title"][:52], r["own_price_now"],
            r["comp_price"], r["delta"]))

    # --- comparison file: every matched product ---
    comp_path = "%s-comparison.csv" % args.out_prefix
    with open(comp_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Own Product", "Handle", "Own Price Now",
                    "Own Compare-at Now", "Competitor Product",
                    "Competitor Price", "Delta", "Size (ml)",
                    "Size Assumed"])
        for r in sorted(rows, key=lambda r: r["own_title"]):
            w.writerow([r["own_title"], r["own_handle"],
                        "%.2f" % r["own_price_now"],
                        r["own_compare_now"] or "",
                        r["comp_title"], "%.2f" % r["comp_price"],
                        "%+.2f" % r["delta"], r["size_ml"],
                        r["size_assumed"]])

    # --- change list: only the rows to apply, in the chosen mode ---
    if args.mode == "only-lower":
        change_rows = [r for r in rows if r["delta"] < 0]
    else:
        change_rows = [r for r in rows if r["delta"] != 0]
    change_path = "%s-change-list.csv" % args.out_prefix
    with open(change_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Product", "Handle",
                    "New Price (%s)" % args.currency,
                    "New Compare-at (%s)" % args.currency,
                    "Own Price Now", "Delta"])
        for r in change_rows:
            new_price = r["comp_price"]
            new_ca = round(new_price * args.compare_at_multiplier, 2)
            w.writerow([r["own_title"], r["own_handle"],
                        "%.2f" % new_price, "%.2f" % new_ca,
                        "%.2f" % r["own_price_now"],
                        "%+.2f" % r["delta"]])

    # --- unmatched file: own-store products with no match + reason ---
    un_path = "%s-unmatched.csv" % args.out_prefix
    with open(un_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Own Product", "Handle", "Size (ml)", "Reason"])
        for p, k, sz, why in unmatched:
            w.writerow([p["title"].split(" \u2013 ")[0], p["handle"],
                        sz, why])

    print("\nMode:", args.mode,
          "| change-list rows:", len(change_rows))
    print("Wrote %s (%d rows)" % (comp_path, len(rows)))
    print("Wrote %s (%d rows)" % (change_path, len(change_rows)))
    print("Wrote %s (%d rows)" % (un_path, len(unmatched)))
    if args.mode == "only-lower" and n_up:
        print("NOTE: %d matched product(s) are currently CHEAPER than the "
              "competitor and were left out of the change list (only-lower "
              "mode). They stay unchanged." % n_up)
    return 0


if __name__ == "__main__":
    sys.exit(main())
