"""Step 1-3: parse RIS, classify by filename, extract DOIs. No downloads, no writes to Literature/."""
import json, os, re, sys
import os
from pathlib import Path

ROOT = Path(os.environ.get("CPUE_SRC", "."))   # set CPUE_SRC to the source collection
LIT = ROOT / "Literature"
LITX = ROOT / "Litx"
OUT = ROOT / "oa-check-output"
OUT.mkdir(exist_ok=True)

# ---------- Step 1: parse the RIS ----------
def parse_ris(path):
    recs, cur = [], None
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9])  - ?(.*)$", raw)
        if not m:
            continue
        tag, val = m.group(1), m.group(2).strip()
        if tag == "TY":
            cur = {"TY": val, "AU": []}
        elif tag == "ER":
            if cur: recs.append(cur); cur = None
        elif cur is not None:
            if tag == "AU":
                cur["AU"].append(val)
            else:
                cur.setdefault(tag, val)
    return recs

ris = parse_ris(LITX / "Exported Items" / "Exported Items.ris")
# key RIS records by the attachment path (L1)
ris_by_file = {}
for r in ris:
    l1 = r.get("L1", "")
    if l1:
        ris_by_file[l1.replace("\\", "/")] = r

# ---------- enumerate files ----------
files = []
for base, label in ((LIT, "Literature"), (LITX, "Litx")):
    for p in sorted(base.rglob("*")):
        if p.is_file():
            files.append(p)

def rel(p): return str(p.relative_to(ROOT)).replace("\\", "/")

# ---------- Step 2: classify ----------
RFMO_PUBLIC = [
    r"^Literature/IATTC/(SAC-|SAR-|OTM-|RVDTT-|BET-01-04|YFT-02-PRES)",
    r"^Literature/IATTC/Vol-\d+-No-\d+-\d{4}-",
    r"^Literature/ICCAT/.*CV0",
    r"^Literature/ICCAT/.*SCRS_\d{4}_",
    r"^Literature/IOTC/IOTC-",
    r"^Literature/WCPFC_SPC/SC\d+-SA-",
    r"^Literature/.*WGEB-03-RD-B",
    r"^Literature/.*SC10-SA-IP-10",
    r"^Literature/.*/CV0\d+\.pdf$",
    r"^Literature/General/IOTC-",
]
RFMO_VERIFY = [
    r"^Literature/WCPFC_ISC/",
    r"^Literature/CCSBT/ESC",
]
JOURNAL = [
    r"^Literature/IATTC/1-s2\.0-S",
    r"^Literature/fsaf114\.pdf$",
    r"^Literature/General/Campbell 2015",
    r"^Literature/General/Ducharme-Barth et al 2022",
    r"^Literature/General/Hoyle et al 2024 CPUE good practices",
    r"^Literature/General/Hsu et al 2022",
    r"^Literature/General/Yang et al 2025",
    r"^Literature/Lazaris et al 2025",
    r"^Literature/Traplines and meka-rings/Garibaldi et al 2024",
    r"^Literature/Traplines and meka-rings/Macias et al 2025",
    r"^Litx/Exported Items/files/31108/",
    # not named in the brief but clearly journal articles by filename:
    r"^Literature/CCSBT/Hoyle et al 2022 CPUE standardization for SBT",
]
UNCERTAIN = [
    r"^Literature/CapMarine-2022",
    r"^Literature/IATTC/Spatio-temporal_modelling_IATTC",
    r"^Literature/ICCAT/ALB/ALB_SA_ENG",
    r"^Literature/ICCAT/SWO/Anon 2022",
    r"^Literature/ICCAT/Sailfish/Ramos-Cartelle et al 2023",
    r"^Literature/ICCAT/BET/ICCAT 2025",
    r"^Literature/ICCAT/BET/(Su & Sung|Urtizberea)",
    r"^Literature/ICCAT/YFT/Satoh & Matsumoto 2017",
    r"^Literature/Traplines and meka-rings/Ochi et al 2025",
    r"^Literature/Traplines and meka-rings/Usui et al 2018 Itoman-type rings fishing method swordfish Japanese",
]
EXCLUDE = [
    r"Usui et al 2018 .*translated\.docx$",
    r"\.xlsx$",
    r"Exported Items\.ris$",
]

def classify(rp):
    for pat in EXCLUDE:
        if re.search(pat, rp): return "excluded"
    for pat in JOURNAL:
        if re.search(pat, rp): return "journal"
    for pat in UNCERTAIN:
        if re.search(pat, rp): return "uncertain"
    for pat in RFMO_PUBLIC:
        if re.search(pat, rp): return "rfmo_public"
    for pat in RFMO_VERIFY:
        if re.search(pat, rp): return "rfmo_verify"
    return "UNMATCHED"

rows = []
for p in files:
    rp = rel(p)
    rows.append({"relative_path": rp, "category": classify(rp), "doi": "", "doi_source": "none",
                 "is_oa": "", "oa_status": "", "best_free_url": "", "notes": ""})

json.dump(rows, open(OUT / "_stage1.json", "w", encoding="utf-8"), indent=1)
from collections import Counter
print(Counter(r["category"] for r in rows))
print("\nUNMATCHED:")
for r in rows:
    if r["category"] == "UNMATCHED": print("  ", r["relative_path"])
