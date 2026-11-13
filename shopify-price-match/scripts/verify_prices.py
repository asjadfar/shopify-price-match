#!/usr/bin/env python3
"""Verify a price-match change list against a fresh products.json.

Checks every row of an approved change list against the store's live
catalog (re-fetched products.json): live price and live compare-at price
must equal the change list's New Price and New Compare-at, row by row.
Optionally also checks that products NOT in the change list stayed
unchanged since a pre-change snapshot.

Usage:
  python3 verify_prices.py change-list.csv fresh-products.json
  python3 verify_prices.py change-list.csv fresh-products.json \
      --before before-products.json

Exit 0 only when every changed product matches and (if --before is
given) no unchanged product moved. Any mismatch prints FAIL and the
exit code is 1 — do not report the job as done until this passes.

The change-list CSV is the format written by match_prices.py:
  Product,Handle,New Price,New Compare-at,Own Price Now,Delta
Column headers may carry a currency label, e.g. "New Price (RM)".
Only the first variant of each product is checked.
"""
import argparse
import csv
import json
import sys


def load_products(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["products"] if isinstance(data, dict) else data


def first_variant_price(p):
    v = p["variants"][0]
    price = float(v["price"])
    ca = v.get("compare_at_price")
    return price, (float(ca) if ca not in (None, "") else None)


def col(row, *names):
    for n in names:
        if n in row:
            return row[n]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("change_list", help="approved change-list CSV")
    ap.add_argument("fresh_json", help="freshly fetched products.json")
    ap.add_argument("--before", default=None,
                    help="pre-change products.json snapshot, to check "
                         "unchanged products stayed unchanged")
    args = ap.parse_args()

    fresh = {p["handle"]: p for p in load_products(args.fresh_json)}

    with open(args.change_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # normalise headers: strip any " (XXX)" currency label
    fieldmap = {}
    for h in reader.fieldnames:
        base = h.split(" (")[0].strip()
        fieldmap[base] = h

    def get(row, base):
        return row.get(fieldmap.get(base, base), "")

    n_ok = n_fail = 0
    for row in rows:
        handle = get(row, "Handle")
        name = get(row, "Product")
        try:
            want_price = float(get(row, "New Price"))
            want_ca_raw = get(row, "New Compare-at")
            want_ca = float(want_ca_raw) if want_ca_raw not in ("", None) else None
        except ValueError:
            print("FAIL | %-52s | bad number in change list" % name[:52])
            n_fail += 1
            continue
        p = fresh.get(handle)
        if p is None:
            print("FAIL | %-52s | handle %s not found in live catalog"
                  % (name[:52], handle))
            n_fail += 1
            continue
        live_price, live_ca = first_variant_price(p)
        problems = []
        if live_price != want_price:
            problems.append("price live %.2f != want %.2f"
                            % (live_price, want_price))
        if want_ca is not None and live_ca != want_ca:
            problems.append("compare-at live %s != want %.2f"
                            % ((" %.2f" % live_ca) if live_ca is not None
                               else "none", want_ca))
        if problems:
            print("FAIL | %-52s | %s" % (name[:52], "; ".join(problems)))
            n_fail += 1
        else:
            n_ok += 1

    print("\nChanged products: %d checked, %d OK, %d FAIL"
          % (len(rows), n_ok, n_fail))

    n_un_ok = n_un_fail = 0
    if args.before:
        before = {p["handle"]: p for p in load_products(args.before)}
        changed_handles = {get(r, "Handle") for r in rows}
        for handle, p in before.items():
            if handle in changed_handles:
                continue
            q = fresh.get(handle)
            if q is None:
                print("FAIL | unchanged product %s missing from live "
                      "catalog" % handle)
                n_un_fail += 1
                continue
            bp, bca = first_variant_price(p)
            lp, lca = first_variant_price(q)
            if bp != lp or bca != lca:
                print("FAIL | unchanged product %s moved: price %.2f -> "
                      "%.2f, compare-at %s -> %s"
                      % (handle, bp, lp,
                         ("%.2f" % bca) if bca is not None else "none",
                         ("%.2f" % lca) if lca is not None else "none"))
                n_un_fail += 1
            else:
                n_un_ok += 1
        print("Unchanged products: %d checked, %d OK, %d FAIL"
              % (n_un_ok + n_un_fail, n_un_ok, n_un_fail))

    if n_fail or n_un_fail:
        print("RESULT: FAIL — fix the failed rows and re-verify.")
        return 1
    print("RESULT: PASS — every changed product is at its new value%s."
          % (" and every unchanged product stayed unchanged"
             if args.before else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
