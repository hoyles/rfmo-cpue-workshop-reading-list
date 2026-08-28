"""Fold verified direct-PDF URLs into the audit, filling best_free_url for RFMO items.

Each org map is {relative_path: url}, built by crawling that organisation's own
document pages and matching on exact filename. Nothing here is constructed by
pattern-guessing a URL.
"""
import csv, json, os
from pathlib import Path

ROOT = Path(os.environ.get("CPUE_SRC", "."))
OUT = ROOT / "oa-check-output"

MAPS = ["_isc_urls.json", "_iotc_urls.json", "_wcpfc_urls.json", "_iattc_urls.json", "_iccat_urls.json"]

urls = {}
for m in MAPS:
    p = OUT / m
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        urls.update(d)
        print(f"  {m}: {len(d)}")

rows = json.loads((OUT / "_final.json").read_text(encoding="utf-8"))
n = 0
for r in rows:
    u = urls.get(r["relative_path"])
    if u and not r["best_free_url"]:
        r["best_free_url"] = u
        n += 1

FIELDS = ["relative_path", "category", "doi", "doi_source", "is_oa", "oa_status", "best_free_url", "notes"]
with open(OUT / "oa_check.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
json.dump(rows, open(OUT / "_final.json", "w", encoding="utf-8"), indent=1)
print(f"filled best_free_url for {n} RFMO documents")
