#!/usr/bin/env python3
"""Audit a JLCPCB BOM against the live JLC component library (read-only, no account).

For every LCSC number in a ``bom.csv`` produced by ``export.py`` this reports

* the library the part is in: ``basic`` (Basic, no setup fee), ``preferred-extended``
  (Preferred Extended, no setup fee for Economic PCBA) or ``extended`` (USD 3 per
  unique part for Economic PCBA), and
* live stock and the lowest price tier.

That turns "are the passives as cheap as possible?" into a check instead of a guess.
The endpoint is the same public one the JLC parts page uses; nothing is uploaded,
reserved or ordered.

Usage:
  python3 scripts/jlcpcb/parts_check.py PCB/main/dist/jlcpcb/bom.csv [--json out.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request

SEARCH = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
EXTENDED_PART_FEE_USD = 3.0
LIBRARY_LABELS = {"base": "basic", "expand": "extended"}


def query(code: str, timeout: float = 30.0):
    body = json.dumps({"currentPage": 1, "pageSize": 10, "keyword": code}).encode()
    request = urllib.request.Request(
        SEARCH, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    rows = payload.get("data", {}).get("componentPageInfo", {}).get("list", [])
    for row in rows:
        if (row.get("componentCode") or "").upper() == code.upper():
            return row
    return None


def classify(row):
    """(label, fee_free, detail) for one JLC search row."""
    if row is None:
        return "unknown", False, "no match in the JLC component library"
    label = LIBRARY_LABELS.get(row.get("componentLibraryType"), "unknown")
    if label == "extended" and row.get("preferredComponentFlag"):
        return "preferred-extended", True, "extended library, Preferred Extended"
    return label, label == "basic", row.get("componentLibraryType")


def audit(bom_path, verbose=True):
    rows = list(csv.DictReader(open(bom_path)))
    seen, report, fee = {}, [], 0.0
    for row in rows:
        code = (row.get("LCSC Part #") or "").strip()
        if not code:
            report.append({"comment": row.get("Comment"), "designators": row.get("Designator"),
                           "lcsc": None, "library": "missing", "fee_free": False})
            continue
        if code not in seen:
            seen[code] = query(code)
        label, fee_free, _ = classify(seen[code])
        price_row = (seen[code] or {}).get("componentPrices") or [{}]
        entry = {
            "comment": row.get("Comment"), "designators": row.get("Designator"),
            "footprint": row.get("Footprint"), "lcsc": code, "quantity": row.get("Quantity"),
            "mpn": row.get("MPN"), "library": label, "fee_free": fee_free,
            "stock": (seen[code] or {}).get("stockCount"),
            "unit_price_usd": price_row[0].get("productPrice"),
        }
        if not fee_free:
            fee += EXTENDED_PART_FEE_USD
        report.append(entry)

    if verbose:
        for entry in report:
            flag = "OK " if entry.get("fee_free") else "FEE"
            print(f"{flag} {entry['library']:18} {str(entry['lcsc']):10} "
                  f"stock={str(entry.get('stock')):>10} ${entry.get('unit_price_usd')!s:>7} "
                  f"{str(entry.get('comment')):22} {entry.get('designators')}")
        charged = [e for e in report if not e.get("fee_free")]
        print(f"\n{len(report)} BOM rows, fee-free {len(report) - len(charged)}, "
              f"charged {len(charged)}, estimated extended-part fee "
              f"${fee:.2f} ({EXTENDED_PART_FEE_USD:.2f}/part)")
    return {"rows": report, "extended_part_fee_usd": fee,
            "fee_per_extended_part_usd": EXTENDED_PART_FEE_USD}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bom", help="bom.csv produced by export.py")
    parser.add_argument("--json", help="also write the audit as JSON")
    args = parser.parse_args()
    result = audit(args.bom)
    if args.json:
        with open(args.json, "w") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
