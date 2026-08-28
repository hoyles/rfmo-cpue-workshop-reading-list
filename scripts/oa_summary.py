"""Write the plain-text summary: counts by category, and the journal items with no free version."""
import json
from collections import Counter
import os
from pathlib import Path

ROOT = Path(os.environ.get("CPUE_SRC", "."))   # set CPUE_SRC to the source collection
OUT = ROOT / "oa-check-output"
rows = json.load(open(OUT / "_final.json", encoding="utf-8"))

L = []
w = L.append
w("OPEN-ACCESS CHECK - Global Joint Tuna RFMO Longline CPUE Technical Workshop")
w("Yokohama, 12-16 October 2026")
w("Source: Literature/ and Litx/ under joint_RFMO_CPUE_meeting (read-only; nothing was modified)")
w("=" * 78)
w("")

counts = Counter(r["category"] for r in rows)
w("COUNTS BY CATEGORY")
w("-" * 78)
order = ["rfmo_public", "rfmo_verify", "journal", "uncertain", "duplicate", "excluded"]
blurb = {
    "rfmo_public": "free from the issuing RFMO; share the org's link",
    "rfmo_verify": "RFMO papers needing a manual permissions check",
    "journal": "journal articles - the Unpaywall lookup targets",
    "uncertain": "could not be resolved from the file; needs a human look",
    "duplicate": "same document already recorded elsewhere in the folder",
    "excluded": "not a reference item, or out of scope per the brief",
}
for c in order:
    w(f"  {c:<14} {counts.get(c,0):>4}   {blurb[c]}")
w(f"  {'TOTAL':<14} {len(rows):>4}   files examined")
w(f"  {'(unique)':<14} {len(rows)-counts.get('duplicate',0)-counts.get('excluded',0):>4}   distinct shareable items")
w("")

unpaywalled = any(r["is_oa"] for r in rows)

w("")
w("JOURNAL ITEMS WITH NO FREE VERSION FOUND")
w("-" * 78)
if not unpaywalled:
    w("  NOT YET DETERMINED - the Unpaywall step has not been run.")
    w("  Run:  python Claude_code/oa_unpaywall.py <your-email@example.org>")
    w("  Unpaywall requires an email as a URL parameter, so it was left for you to supply.")
    w("")
    w("  The 13 journal items and their DOIs are listed below; page-1 licence statements")
    w("  read off the PDFs themselves are given where present.")
    w("")
    for r in rows:
        if r["category"] != "journal":
            continue
        w(f"  {r['relative_path']}")
        w(f"      DOI {r['doi']}  (source: {r['doi_source']})")
        if r["notes"]:
            w(f"      {r['notes']}")
    w("")
else:
    stuck = [r for r in rows if r["category"] == "journal" and r["is_oa"] != "TRUE"]
    if not stuck:
        w("  None - every journal item has a free version. Nothing needs a workaround.")
    else:
        w(f"  {len(stuck)} of {counts['journal']} journal items have no free version.")
        w("  These need a different solution: an author-supplied accepted manuscript, an")
        w("  Elsevier Share Link, or a DOI link with a note that access varies.")
        w("")
        for r in stuck:
            w(f"  {r['relative_path']}")
            w(f"      DOI {r['doi']}    https://doi.org/{r['doi']}")
            w(f"      is_oa={r['is_oa']} oa_status={r['oa_status'] or '-'}")
            if r["notes"]:
                w(f"      {r['notes']}")
        w("")
    free = [r for r in rows if r["category"] == "journal" and r["is_oa"] == "TRUE"]
    if free:
        w("")
        w("JOURNAL ITEMS WITH A FREE VERSION")
        w("-" * 78)
        for r in free:
            w(f"  {r['relative_path']}")
            w(f"      {r['oa_status']}  {r['best_free_url']}")
        w("")

w("")
w("ITEMS NEEDING A HUMAN DECISION")
w("-" * 78)
w("")
w("A. ISC working papers carrying a do-not-cite notice on page 1")
isc = [r for r in rows if r["category"] == "rfmo_verify" and "PAGE 1 NOTICE PRESENT" in r["notes"]]
w(f"   {len(isc)} of the {counts.get('rfmo_verify',0)} rfmo_verify items. All are ISC Shark WG papers.")
w("   Wording: 'Working document submitted to the ISC ... Document not to be cited")
w("   without author's permission.' Seek author permission before circulating these.")
for r in isc:
    w(f"     {r['relative_path']}")
w("")
w("B. ISC working papers with NO such notice anywhere in the document")
clean = [r for r in rows if r["category"] == "rfmo_verify"
         and r["relative_path"].startswith("Literature/WCPFC_ISC/") and "PAGE 1 NOTICE PRESENT" not in r["notes"]]
w(f"   {len(clean)} items (ALBWG, BILLWG and PBFWG papers). Scanned in full, not just page 1.")
w("   Lower risk, but ISC posts these on isc.fra.go.jp - link there rather than resharing.")
w("")
w("C. CCSBT ESC papers")
ccsbt = [r for r in rows if r["relative_path"].startswith("Literature/CCSBT/ESC")]
w(f"   {len(ccsbt)} items. None carries a restriction notice on the document itself, but")
w("   CCSBT may limit ESC papers to members. Per the brief this was flagged only, not")
w("   tested. Confirm with the CCSBT Secretariat before sharing.")
for r in ccsbt:
    w(f"     {r['relative_path']}")
w("")
w("D. Unresolved from the file alone")
for r in rows:
    if r["category"] == "uncertain":
        w(f"   {r['relative_path']}")
        w(f"     {r['notes']}")
        w("")

w("")
w("CORRECTIONS TO THE ASSUMPTIONS IN THE TASK BRIEF")
w("-" * 78)
w("")
w("1. The Zotero export is at Litx/Exported Items/, not ICCAT/Exported Items/.")
w("")
w("2. It holds 34 records but only ONE DOI, and that DOI is attached to the wrong")
w("   PDF. The record 'Mourato et al. 2014 - Short-term movements ... sailfish'")
w("   (DOI 10.1590/1982-0224-20130102, Neotropical Ichthyology) has as its attachment")
w("   a byte-identical copy of ICCAT/Sailfish/Mourato et al 2023 Sailfish Brazil")
w("   CV080080226.pdf - an ICCAT Collective Volume paper on Brazilian sailfish catch")
w("   rates. The brief listed this file as a journal-article lookup target; it is not")
w("   one. The DOI was not used, per the rule against guessing. The 2014 article is")
w("   not present in this folder.")
w("")
w("3. Three files the brief listed as journal articles are ICCAT Collective Volume")
w("   papers, free from iccat.int, with no DOI:")
w("     Garibaldi et al 2024  -> Collect. Vol. Sci. Pap. ICCAT 81(7), SCRS/2024/064")
w("     Macias et al 2025     -> Collect. Vol. Sci. Pap. ICCAT 82(6), SCRS/2025/098")
w("     Litx .../31108/Mourato -> Collect. Vol. Sci. Pap. ICCAT 80(8), SCRS/2023/092")
w("   That reduces the lookup set from 16 to 13.")
w("")
w("4. One journal article was not covered by any rule in the brief:")
w("     Literature/CCSBT/Hoyle et al 2022 CPUE standardization for SBT in the Korean")
w("     longline fishery.pdf - PeerJ, CC-BY 4.0, stated open access on page 1.")
w("   It sits in CCSBT/ but is not an ESC paper. Added to the journal set.")
w("")
w("5. The do-not-cite notice is not spread across ISC generally. It appears on 17 of")
w("   51 documents, and every one is a Shark Working Group paper. ALBWG, BILLWG and")
w("   PBFWG papers carry no such notice.")
w("")
w("6. Traplines and meka-rings/CV08107064.pdf is byte-identical to the Garibaldi et")
w("   al 2024 file in the same folder - a duplicate the brief did not list.")
w("")
w("7. The Ochi et al. 2025 meka-ring trio: the Traplines/ copy and WGEB-03-RD-B are")
w("   byte-identical; the IOTC copy is the same text with an IOTC-2025-WPEB21(AS)-26")
w("   header. The IOTC copy is recorded as primary.")
w("")
w("8. Literature/Traplines and meka-rings/Usui et al 2018 ... Japanese.pdf is the")
w("   copyrighted Japanese original of the translation the brief excludes. It needs")
w("   the same permission handling and is flagged uncertain, not shareable.")
w("")
w("METHOD NOTES")
w("-" * 78)
w("  - No file in Literature/ or Litx/ was modified, renamed, moved or deleted.")
w("  - No full-text PDF was downloaded.")
w("  - Duplicates were established by MD5 over file contents, not by filename.")
w("  - Every PDF opened had a text layer; no OCR was needed and none was run.")
w("  - No DOI was guessed or inferred from a filename.")

(OUT / "oa_check_summary.txt").write_text("\n".join(L), encoding="utf-8")
print("\n".join(L))
