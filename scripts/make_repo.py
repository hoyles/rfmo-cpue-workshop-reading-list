"""Build the shareable GitHub repo from the audit CSV.

Links-only for RFMO grey literature; PDFs committed only for CC-BY articles.
Nothing is read from outside Literature/ and Litx/, and nothing there is modified.
"""
import csv, json, re, shutil
from collections import defaultdict
import os
from pathlib import Path

SRC = Path(os.environ.get("CPUE_SRC", "."))    # set CPUE_SRC to the source collection
REPO = Path(os.environ.get("CPUE_REPO", "./out"))  # where to build the repo

rows = list(csv.DictReader(open(SRC / "oa-check-output/oa_check.csv", encoding="utf-8-sig")))

# ---------------------------------------------------------------- layout
for d in ("data", "pdfs", "scripts"):
    (REPO / d).mkdir(parents=True, exist_ok=True)

shutil.copy2(SRC / "oa-check-output/oa_check.csv", REPO / "data/oa_check.csv")
shutil.copy2(SRC / "oa-check-output/oa_check_summary.txt", REPO / "data/oa_check_summary.txt")
def publish_script(name):
    """Copy a pipeline script, replacing local absolute paths with an env var.

    The working copies hard-code the source collection; the published copies must
    not leak a local filesystem layout.
    """
    s = (SRC / "Claude_code" / name).read_text(encoding="utf-8")
    s = re.sub(r'ROOT = Path\(r"[A-Za-z]:/[^"]*"\)',
               'ROOT = Path(os.environ.get("CPUE_SRC", "."))   # set CPUE_SRC to the source collection', s)
    s = re.sub(r'SRC = Path\(r"[A-Za-z]:/[^"]*"\)',
               'SRC = Path(os.environ.get("CPUE_SRC", "."))    # set CPUE_SRC to the source collection', s)
    s = re.sub(r'REPO = Path\(r"[A-Za-z]:/[^"]*"\)',
               'REPO = Path(os.environ.get("CPUE_REPO", "./out"))  # where to build the repo', s)
    if "os.environ" in s and not re.search(r"^import os$", s, re.M):
        s = re.sub(r"^(from pathlib import Path)$", r"import os\n\1", s, count=1, flags=re.M)
    assert not re.search(r"[A-Za-z]:/Users", s), f"local path survived in {name}"
    (REPO / "scripts" / name).write_text(s, encoding="utf-8")


for s in ("oa_check.py", "oa_extract.py", "oa_assemble.py", "oa_unpaywall.py", "oa_summary.py", "make_repo.py"):
    publish_script(s)

# ---------------------------------------------------------------- CC-BY PDFs
CCBY = {
    "Literature/CCSBT/Hoyle et al 2022 CPUE standardization for SBT in the Korean longline fishery.pdf": dict(
        out="Hoyle-etal-2022-SBT-Korean-longline-CPUE.pdf",
        cite="Hoyle SD, Lee SI, Kim DN (2022) CPUE standardization for southern bluefin tuna (Thunnus maccoyii) in the Korean tuna longline fishery, accounting for spatiotemporal variation in targeting through data exploration and clustering. PeerJ 10:e13951.",
        doi="10.7717/peerj.13951", lic="CC BY 4.0", pub="PeerJ"),
    "Literature/fsaf114.pdf": dict(
        out="Wu-etal-2025-spatially-varying-coefficients-DCM.pdf",
        cite="Wu H-H, Thorson JT, Hilborn R, Chang Y (2025) Spatially varying coefficients improve discrete choice models for tuna purse seine fisheries in the Western-Central Pacific. ICES Journal of Marine Science 82(7):fsaf114.",
        doi="10.1093/icesjms/fsaf114", lic="CC BY 4.0", pub="ICES Journal of Marine Science (OUP)"),
    "Literature/General/Ducharme-Barth et al 2022 Impacts of fishery-dependent spatial sampling on CPUE - simulation & application.pdf": dict(
        out="Ducharme-Barth-etal-2022-spatial-sampling-CPUE.pdf",
        cite="Ducharme-Barth ND, Gruss A, Vincent MT, Kiyofuji H, Aoki Y, Pilling G, Hampton J, Thorson JT (2022) Impacts of fisheries-dependent spatial sampling patterns on catch-per-unit-effort standardization: A simulation study and fishery application. Fisheries Research 246:106169.",
        doi="10.1016/j.fishres.2021.106169", lic="CC BY 4.0", pub="Fisheries Research (Elsevier)"),
    "Literature/Lazaris et al 2025 Multiple gears and preferential sampling.pdf": dict(
        out="Lazaris-etal-2025-multiple-gears-preferential-sampling.pdf",
        cite="Lazaris A, Tserpes G, Kavadas S, Tzanatos E (2025) Standardization of commercial catch data from multiple gears in mixed fisheries accounting for preferential sampling, catchability, and fishing effort. Fisheries Research 284:107305.",
        doi="10.1016/j.fishres.2025.107305", lic="CC BY 4.0", pub="Fisheries Research (Elsevier)"),
}
for src_rel, m in CCBY.items():
    shutil.copy2(SRC / src_rel, REPO / "pdfs" / m["out"])

A = ["# Attribution for the PDFs in this directory", "",
     "Each file below is redistributed under a Creative Commons Attribution licence,",
     "which permits redistribution provided the work is attributed. The licence is the",
     "publisher's, not this repository's. Cite the original article, not this repo.", ""]
for m in CCBY.values():
    A += [f"## {m['out']}", "", f"- {m['cite']}", f"- DOI: https://doi.org/{m['doi']}",
          f"- Published in: {m['pub']}", f"- Licence: **{m['lic']}**", ""]
(REPO / "pdfs/ATTRIBUTION.md").write_text("\n".join(A), encoding="utf-8")

# ---------------------------------------------------------------- reading list
PORTAL = {  # verified 200 on 2026-08-28 unless noted
    "IATTC":  ("https://www.iattc.org/en-US/Meetings/Documents", True),
    "ICCAT":  ("https://www.iccat.int/en/pubs_CVSP.html", True),
    "IOTC":   ("https://iotc.org/documents", True),
    "WCPFC":  ("https://meetings.wcpfc.int/", True),
    "SPC":    ("https://fame.spc.int/", True),
    "CCSBT":  ("https://www.ccsbt.org/", True),
    "ISC":    ("https://isc.fra.go.jp/", False),
}


def org_of(rp):
    if rp.startswith("Literature/IATTC/"): return "IATTC"
    if rp.startswith("Literature/ICCAT/"): return "ICCAT"
    if rp.startswith("Literature/IOTC/"): return "IOTC"
    if rp.startswith("Literature/WCPFC_ISC/"): return "ISC"
    if rp.startswith("Literature/WCPFC_SPC/"): return "SPC"
    if rp.startswith("Literature/CCSBT/"): return "CCSBT"
    if "IOTC-" in rp: return "IOTC"
    if re.search(r"/SC\d+-SA-|SC10-SA-", rp): return "SPC"
    if "WGEB-" in rp: return "WCPFC"
    if "CV0" in rp or "SCRS" in rp: return "ICCAT"
    return "ICCAT" if rp.startswith("Literature/Traplines") else "other"


def docid(rp, notes):
    """Document identifier, read off page 1 where available, else parsed from the filename."""
    m = re.search(r"(SCRS/\d{4}/\d+)", notes)
    if m: return m.group(1)
    n = Path(rp).name
    # ICCAT Collective Volume: CV + volume(3) + issue(2) + page(remainder)
    m = re.search(r"CV(\d{3})(\d{2})(\d{2,4})", n)
    if m:
        return f"Collect. Vol. Sci. Pap. ICCAT {int(m.group(1))}({int(m.group(2))}): {int(m.group(3))}"
    m = re.search(r"(SCRS[_ ]\d{4}[_ ]\d+)", n)
    if m: return m.group(1).replace("_", "/").replace(" ", "/")
    for pat in (r"^(IOTC-\d{4}-[A-Za-z0-9()]+-[A-Za-z0-9]+)", r"^(SAC-\d+-[A-Z0-9]+(?:-[A-Z])?)",
                r"^(SAR-\d+(?:-\d+)?)", r"^(OTM-\d+-[A-Z]+)", r"^(RVDTT-\d+-[A-Z0-9]+)",
                r"^(BET-\d+-\d+)", r"^(YFT-\d+-[A-Z]+)", r"^(SC\d+-SA-[A-Z]+-\d+)",
                r"^(ISC[_\-]?\d+[_\-][A-Za-z]+[A-Z0-9_\-]*?)(?:_[A-Z][a-z])", r"^(ISC[_\-]?\d+[_\-][A-Za-z0-9_\-]+)",
                r"^(\d{4}_ISC_[A-Z0-9\-_]+)", r"^(ESC\d+_[A-Za-z0-9]+)", r"^(WGEB-\d+-RD-[A-Z])",
                r"^(Vol-\d+-No-\d+-\d{4})"):
        m = re.match(pat, n)
        if m: return m.group(1)
    return ""


def title_of(rp, d=""):
    t = Path(rp).stem
    if d:
        # drop a leading copy of the identifier so it is not printed twice
        head = re.escape(d.replace("/", "[_/ ]").replace("(", r"\(").replace(")", r"\)"))
        t = re.sub(r"^" + head.replace("\\[_/ \\]", "[_/ ]") + r"[ _\-]*", "", t)
    t = re.sub(r"\s*-\s*main$", "", t)
    t = re.sub(r"^CV\d{7,}$", "", t)
    if " " not in t or t.count("-") >= 4:
        t = t.replace("-", " ")
    t = re.sub(r"[_]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -_")
    return t or Path(rp).stem


# Real titles for the journal set: embedded PDF metadata where it holds a title,
# otherwise read off page 1. Never invented.
JOURNAL_TITLE = json.loads((SRC / "oa-check-output/_journal_titles.json").read_text(encoding="utf-8"))
JOURNAL_TITLE.update({  # metadata absent or unusable; taken from page 1
    "Literature/IATTC/1-s2.0-S016578360300002X-main.pdf":
        "Fitting fisheries models to standardised CPUE abundance indices",
    "Literature/IATTC/1-s2.0-S0165783604001638-main.pdf":
        "Standardizing catch and effort data: a review of recent approaches",
    "Literature/CCSBT/Hoyle et al 2022 CPUE standardization for SBT in the Korean longline fishery.pdf":
        "CPUE standardization for southern bluefin tuna (Thunnus maccoyii) in the Korean tuna "
        "longline fishery, accounting for spatiotemporal variation in targeting through data "
        "exploration and clustering",
})

live = [r for r in rows if r["category"] not in ("duplicate", "excluded")]
L = []
w = L.append
w("# Reading list — Global Joint Tuna RFMO Longline CPUE Technical Workshop")
w("")
w("Yokohama, 12–16 October 2026.")
w("")
w("Titles are taken from the source filenames, which were curated by hand; document")
w("identifiers are parsed from the filename or read off page 1 of the PDF. Where an")
w("item is not linked directly, search the issuing organisation's document portal for")
w("the identifier given.")
w("")
w("| Organisation | Document portal |")
w("|---|---|")
for org, (u, ok) in PORTAL.items():
    w(f"| {org} | [{u}]({u}){'' if ok else ' — not reachable when checked; confirm before circulating'} |")
w("")
w("---")
w("")

# --- journals
w("## Journal articles")
w("")
free = [r for r in live if r["category"] == "journal" and r["is_oa"] == "TRUE"]
shut = [r for r in live if r["category"] == "journal" and r["is_oa"] != "TRUE"]
w(f"### Freely available ({len(free)})")
w("")
for r in sorted(free, key=lambda x: JOURNAL_TITLE.get(x["relative_path"], "")):
    lic = "CC BY" if "cc-by" in r["notes"] else ""
    inrepo = next((m["out"] for k, m in CCBY.items() if k == r["relative_path"]), None)
    w(f"- **{JOURNAL_TITLE.get(r['relative_path']) or title_of(r['relative_path'])}**  ")
    w(f"  [doi.org/{r['doi']}](https://doi.org/{r['doi']}) · free: [{r['oa_status']}]({r['best_free_url']})"
      + (f" · {lic}" if lic else ""))
    if inrepo:
        w(f"  · in this repo: [`pdfs/{inrepo}`](pdfs/{inrepo})")
w("")
w(f"### Paywalled — not redistributable ({len(shut)})")
w("")
w("Access varies by institution. These need an author-supplied accepted manuscript,")
w("an Elsevier Share Link, or simply the DOI with a note that access varies.")
w("")
for r in sorted(shut, key=lambda x: JOURNAL_TITLE.get(x["relative_path"], "")):
    w(f"- **{JOURNAL_TITLE.get(r['relative_path']) or title_of(r['relative_path'])}**  ")
    w(f"  [doi.org/{r['doi']}](https://doi.org/{r['doi']}) · {r['oa_status']}")
w("")

# --- RFMO public
w("## RFMO documents — free from the issuing organisation")
w("")
w("Not mirrored here. Each remains published by the organisation that issued it.")
w("")
pub = defaultdict(list)
for r in live:
    if r["category"] == "rfmo_public":
        pub[org_of(r["relative_path"])].append(r)
for org in sorted(pub):
    w(f"### {org} ({len(pub[org])})")
    w("")
    for r in sorted(pub[org], key=lambda x: x["relative_path"]):
        d = docid(r["relative_path"], r["notes"])
        w(f"- {title_of(r['relative_path'], d)}" + (f" — `{d}`" if d else ""))
    w("")

# --- verify
w("## RFMO documents needing a permissions check before circulation")
w("")
isc_n = [r for r in live if r["category"] == "rfmo_verify" and "PAGE 1 NOTICE PRESENT" in r["notes"]]
isc_c = [r for r in live if r["category"] == "rfmo_verify" and r["relative_path"].startswith("Literature/WCPFC_ISC/") and "PAGE 1 NOTICE PRESENT" not in r["notes"]]
ccs = [r for r in live if r["relative_path"].startswith("Literature/CCSBT/ESC")]
w(f"**{len(isc_n)} ISC Shark Working Group papers carry a notice on page 1:** *“Working document")
w("submitted to the ISC … Document not to be cited without author's permission.”* Author")
w("permission is needed before these are circulated.")
w("")
for r in sorted(isc_n, key=lambda x: x['relative_path']):
    _d = docid(r['relative_path'], r['notes'])
    w(f"- {title_of(r['relative_path'], _d)}" + (f" — `{_d}`" if _d else ""))
w("")
w(f"**{len(isc_c)} other ISC papers** (ALBWG, BILLWG, PBFWG) carry no such notice anywhere in")
w("the document. Link to the ISC site rather than resharing the files.")
w("")
w(f"**{len(ccs)} CCSBT ESC papers.** None carries a restriction notice, but CCSBT may limit ESC")
w("papers to members — confirm with the CCSBT Secretariat.")
w("")
for r in sorted(ccs, key=lambda x: x["relative_path"]):
    _d = docid(r["relative_path"], r["notes"])
    w(f"- {title_of(r['relative_path'], _d)}" + (f" — `{_d}`" if _d else ""))
w("")

# --- uncertain
w("## Unresolved — excluded from the list pending a decision")
w("")
for r in live:
    if r["category"] == "uncertain":
        w(f"- **{title_of(r['relative_path'])}**  ")
        w(f"  {r['notes']}")
        w("")

(REPO / "reading-list.md").write_text("\n".join(L), encoding="utf-8")
print("reading-list.md:", len(L), "lines")
print("live items:", len(live), "| journal free:", len(free), "| journal closed:", len(shut))
print("rfmo_public by org:", {k: len(v) for k, v in sorted(pub.items())})
