"""Step 4: query Unpaywall for each journal DOI and fill is_oa / oa_status / best_free_url.

Usage:  python oa_unpaywall.py you@example.org

Unpaywall requires an email as a query parameter; it is sent in the URL. Rewrites
oa-check-output/oa_check.csv in place and regenerates the summary.
"""
import csv, json, sys, time, urllib.error, urllib.parse, urllib.request
import os
from pathlib import Path

ROOT = Path(os.environ.get("CPUE_SRC", "."))   # set CPUE_SRC to the source collection
OUT = ROOT / "oa-check-output"

if len(sys.argv) < 2 or "@" not in sys.argv[1]:
    sys.exit("Give an email address: python oa_unpaywall.py you@example.org")
EMAIL = sys.argv[1]

rows = json.load(open(OUT / "_final.json", encoding="utf-8"))


def query(doi):
    url = "https://api.unpaywall.org/v2/" + urllib.parse.quote(doi, safe="") \
          + "?" + urllib.parse.urlencode({"email": EMAIL})
    req = urllib.request.Request(url, headers={"User-Agent": "rfmo-cpue-reading-list/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), ""
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}" + (" (DOI not in Unpaywall)" if e.code == 404 else "")
    except Exception as e:
        return None, repr(e)


n = 0
for r in rows:
    if r["category"] != "journal" or not r["doi"]:
        continue
    n += 1
    data, err = query(r["doi"])
    if data is None:
        r["is_oa"] = "lookup_failed"
        r["notes"] = (r["notes"] + " " if r["notes"] else "") + f"Unpaywall: {err}."
        print(f"  ! {r['doi']}  {err}")
    else:
        r["is_oa"] = "TRUE" if data.get("is_oa") else "FALSE"
        r["oa_status"] = data.get("oa_status") or ""
        loc = data.get("best_oa_location") or {}
        r["best_free_url"] = loc.get("url_for_pdf") or loc.get("url") or ""
        bits = []
        if data.get("journal_name"):
            bits.append(data["journal_name"])
        if loc.get("host_type"):
            bits.append("host: " + loc["host_type"])
        if loc.get("license"):
            bits.append("licence: " + loc["license"])
        if bits:
            r["notes"] = (r["notes"] + " " if r["notes"] else "") + "Unpaywall: " + "; ".join(bits) + "."
        print(f"  {'OA ' if data.get('is_oa') else '-- '} {r['doi']:<38} {data.get('oa_status',''):<8} {r['best_free_url'][:70]}")
    time.sleep(1.0)

FIELDS = ["relative_path", "category", "doi", "doi_source", "is_oa", "oa_status", "best_free_url", "notes"]
with open(OUT / "oa_check.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
json.dump(rows, open(OUT / "_final.json", "w", encoding="utf-8"), indent=1)
print(f"\nQueried {n} DOIs. CSV updated.")

import subprocess
subprocess.run([sys.executable, str(ROOT / "Claude_code" / "oa_summary.py")])
