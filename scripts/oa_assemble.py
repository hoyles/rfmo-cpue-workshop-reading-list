"""Assemble the final CSV. Applies the content-based reclassifications and duplicate resolution."""
import csv, hashlib, json, re, sys, warnings
import os
from pathlib import Path
warnings.filterwarnings("ignore")

ROOT = Path(os.environ.get("CPUE_SRC", "."))   # set CPUE_SRC to the source collection
OUT = ROOT / "oa-check-output"
rows = json.load(open(OUT / "_stage1.json", encoding="utf-8"))
s2 = json.load(open(OUT / "_stage2.json", encoding="utf-8"))


# ---- duplicate map: duplicate_path -> primary_path (md5 identity + the brief's known list)
def md5(p):
    return hashlib.md5(p.read_bytes()).hexdigest()


by_hash = {}
for r in rows:
    p = ROOT / r["relative_path"]
    if p.suffix.lower() != ".pdf":
        continue
    by_hash.setdefault(md5(p), []).append(r["relative_path"])


def prefer(paths):
    """Primary = the copy in Literature/ with the most descriptive filename."""
    lit = [p for p in paths if p.startswith("Literature/")]
    pool = lit or paths
    named = [p for p in pool if not re.match(r"^.*/CV\d+\.pdf$", p)]
    return sorted(named or pool)[0]


dup_of = {}
for h, paths in by_hash.items():
    if len(paths) > 1:
        prim = prefer(paths)
        for p in paths:
            if p != prim:
                dup_of[p] = prim

# content-identical but not byte-identical (the brief's known duplicates)
OCHI = "Literature/IOTC/IOTC-2025-WPEB21AS-26_mekaring_Ochi_etal.pdf"
dup_of["Literature/Traplines and meka-rings/Ochi et al 2025 Info about ring-shasped branchline meka-ring in pelagic longline fisheries.pdf"] = OCHI
dup_of["Literature/Traplines and meka-rings/WGEB-03-RD-B_Ring-shaped-branch-lines-(meka-ring)-in-pelagic-longline-fisheries.pdf"] = OCHI
dup_of["Literature/WCPFC_SPC/SC20-SA-IP-19_IOTC-2024-WPTT26DP-16rev3_Effort_creep in tuna assessments_0.pdf"] = "Literature/General/IOTC-2024-WPTT26DP-16rev3_-_Effort_creep.pdf"

# ---- reclassifications established by reading page 1 ----
RECLASS = {
    "Literature/Traplines and meka-rings/Garibaldi et al 2024 New challenge for assessing swordfish - use of innovative fishing gear.pdf": (
        "rfmo_public",
        "NOT a journal article despite the brief. Page 1 reads: Collect. Vol. Sci. Pap. ICCAT, 81(7), SCRS/2024/064: 1-9 (2024). ICCAT Collective Volume paper, free from iccat.int. No DOI.",
    ),
    "Literature/Traplines and meka-rings/Macias et al 2025 Spatiotemporal dbns and bycatch with longlines using traplines in the western mediterranean.pdf": (
        "rfmo_public",
        "NOT a journal article despite the brief. Page 1 reads: Collect. Vol. Sci. Pap. ICCAT, 82(6), SCRS/2025/098: 1-16 (2025). ICCAT Collective Volume paper, free from iccat.int. No DOI.",
    ),
    "Literature/ICCAT/ALB/ALB_SA_ENG.pdf": (
        "rfmo_public",
        "Report of the 2023 ICCAT Atlantic Albacore Stock Assessment Meeting (incl. MSE), hybrid, Madrid, 26-29 June 2023. ICCAT SCRS meeting report.",
    ),
    "Literature/ICCAT/BET/ICCAT 2025 Data prep meeting report for bigeye CV082050005.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 82(5), SCRS/2025/005: 1-96 (2025).",
    ),
    "Literature/ICCAT/BET/ICCAT 2025 Report of bigeye stock assessment meeting CV082050011.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 82(5), SCRS/2025/011: 1-87 (2025).",
    ),
    "Literature/ICCAT/BET/Su & Sung 2025 Chinese Taipei longline CPUE for bigeye CV082050089.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 82(5), SCRS/2025/089: 1-14 (2025).",
    ),
    "Literature/ICCAT/BET/Urtizberea et al 2025 SS assessment Atlantic bigeye tuna CV082050151.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 82(5), SCRS/2025/151: 1-28 (2025).",
    ),
    "Literature/ICCAT/Sailfish/Ramos-Cartelle et al 2023 Sailfish Spain.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 80(8): 359-370 (2023), SCRS/2023/079. Filename carries no CV number, so no filename rule matched it.",
    ),
    "Literature/ICCAT/SWO/Anon 2022 SWO data prep.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 79(2): 001-133 (2022), SCRS/2022/003.",
    ),
    "Literature/ICCAT/SWO/Anon 2022 SWO stock assessment.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 79(2): 392-564 (2022), SCRS/2022/012.",
    ),
    "Literature/ICCAT/YFT/Satoh & Matsumoto 2017 Compare YFT catch effort & size data between NRIFSF and ICCAT databases CV073010318.pdf": (
        "rfmo_public",
        "Collect. Vol. Sci. Pap. ICCAT, 73(1): 318-322 (2017), SCRS/2016/037.",
    ),
    "Litx/Exported Items/files/31108/Mourato et al. - 2014 - Short-term movements and habitat preferences of sailfish, Istiophorus platypterus (Istiophoridae), a.pdf": (
        "duplicate",
        "ZOTERO METADATA MISMATCH - the one RIS record carrying a DOI. The RIS claims Mourato et al. 2014, Neotropical Ichthyology, DOI 10.1590/1982-0224-20130102. The attached PDF is actually CATCH RATES OF SAILFISH FROM BRAZILIAN LONGLINE FISHERIES IN THE WESTERN ATLANTIC (1991-2022), SCRS/2023/092, Collect. Vol. Sci. Pap. ICCAT 80(8): 226-235, byte-identical to the ICCAT/Sailfish copy. The RIS DOI was NOT used. The 2014 journal article is not in this folder.",
    ),
    "Literature/CapMarine-2022.-Stewart-Norman-Dave-Japp-Jodie-Reed-and-Colin-Attwood.-Investigating-RFMO-Bycatch-Observer-Coverage-in-Tuna-Longline-Fisheries..pdf": (
        "uncertain",
        "Consultancy report, not a journal article. Capricorn Marine Environmental (Pty) Ltd, Cape Town, 30 September 2022, contracted by THE PEW CHARITABLE TRUSTS. No DOI, no ISBN, and no distribution or confidentiality statement in the front matter. MANUAL CHECK: confirm Pew published it publicly, and link to their copy.",
    ),
    "Literature/IATTC/Spatio-temporal_modelling_IATTC.pdf": (
        "uncertain",
        "IATTC background note titled 'Spatio-temporal modelling at the IATTC'. No document number, no date, no author list, no DOI, so the issuing page cannot be identified from the file. MANUAL CHECK: locate on iattc.org or substitute a numbered IATTC document.",
    ),
    "Literature/Traplines and meka-rings/Usui et al 2018 Itoman-type rings fishing method swordfish Japanese.pdf": (
        "uncertain",
        "Japanese-language original, Kanagawa Prefectural Fisheries Technology Center Research Report No. 9 (2018), accepted 2018-01-24. This is the source article for the 'translated.docx' the brief puts out of scope; it needs the same permission handling. Recommend excluding from the participant list.",
    ),
    "Literature/CCSBT/Hoyle et al 2022 CPUE standardization for SBT in the Korean longline fishery.pdf": (
        "journal",
        "Not covered by any filename rule in the brief - sits in CCSBT/ but is not an ESC paper. PeerJ; page 1 states Creative Commons CC-BY 4.0, OPEN ACCESS.",
    ),
}

NOTES_EXTRA = {
    "Literature/General/Ducharme-Barth et al 2022 Impacts of fishery-dependent spatial sampling on CPUE - simulation & application.pdf":
        "Page 1 states: open access under the CC BY license.",
    "Literature/Lazaris et al 2025 Multiple gears and preferential sampling.pdf":
        "Page 1 states: open access under the CC BY license.",
    "Literature/General/Hoyle et al 2024 CPUE good practices.pdf":
        "Page 1 states: (c) 2023 Elsevier B.V., all rights reserved - no OA statement on the article itself.",
    "Literature/General/Hsu et al 2022 Influence of spatial treatments on catch-per-unit-effort standardization - Saury example.pdf":
        "Page 1 states: (c) 2022 Elsevier B.V., all rights reserved - no OA statement on the article itself.",
    "Literature/IATTC/1-s2.0-S0165783624001759-main.pdf":
        "Page 1 states: (c) 2024 Elsevier B.V., all rights reserved.",
    "Literature/General/IOTC-2024-WPTT26DP-16rev3_-_Effort_creep.pdf":
        "Primary record for the effort-creep paper; WCPFC_SPC/SC20-SA-IP-19 is the same document.",
    OCHI:
        "Primary record for Ochi et al. 2025 (meka-ring); the Traplines/ copy and WGEB-03-RD-B are the same document.",
    "Literature/ICCAT/Sailfish/Mourato et al 2023 Sailfish Brazil CV080080226.pdf":
        "Primary record. See the Litx/Exported Items 31108 row - the Zotero export files this PDF under the wrong title and DOI.",
}

# corrected DOI where the regex clipped a bracketed suffix
DOI_FIX = {
    "Literature/IATTC/1-s2.0-S016578360300002X-main.pdf": ("10.1016/S0165-7836(03)00002-X", "pdf_metadata")
}

NOTICE = re.compile(r"(not to be cited without|do not cite without)", re.I)

final = []
for r in rows:
    rp = r["relative_path"]
    cat, note = r["category"], ""
    if rp in RECLASS:
        cat, note = RECLASS[rp]
    if rp in dup_of and cat != "excluded":
        cat = "duplicate"
        note = (note + " " if note else "") + "Duplicate of: " + dup_of[rp]
    if rp in NOTES_EXTRA:
        note = (note + " " if note else "") + NOTES_EXTRA[rp]

    doi, src = "", "none"
    if cat == "journal":
        v = s2.get(rp, {})
        doi, src = v.get("doi", ""), v.get("doi_source", "none")
        if rp in DOI_FIX:
            doi, src = DOI_FIX[rp]
        if not doi:
            src = "none"

    if cat == "rfmo_verify":
        v = s2.get(rp, {})
        p1 = v.get("p1", "") + v.get("docite_ctx", "")
        if NOTICE.search(p1):
            note = (note + " " if note else "") + "PAGE 1 NOTICE PRESENT: 'Working document submitted to the ISC ... Document not to be cited without author's permission.' Seek author permission before circulating."
        elif rp.startswith("Literature/CCSBT/"):
            note = (note + " " if note else "") + "CCSBT ESC meeting paper. No restriction notice on the document itself, but CCSBT may limit ESC papers to members - verify with the CCSBT Secretariat."
        else:
            note = (note + " " if note else "") + "ISC working document; no do-not-cite notice found anywhere in the document."

    if cat == "excluded":
        if rp.endswith(".docx"):
            note = "Out of scope per the brief: translation of a copyrighted Japanese original; needs separate permission handling."
        elif rp.endswith(".ris"):
            note = "Not a reference item (the Zotero export file itself)."
        else:
            note = "Not a reference item (spreadsheet)."

    final.append({"relative_path": rp, "category": cat, "doi": doi, "doi_source": src,
                  "is_oa": "", "oa_status": "", "best_free_url": "", "notes": note.strip()})

FIELDS = ["relative_path", "category", "doi", "doi_source", "is_oa", "oa_status", "best_free_url", "notes"]
with open(OUT / "oa_check.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(final)
json.dump(final, open(OUT / "_final.json", "w", encoding="utf-8"), indent=1)

from collections import Counter
print(dict(Counter(r["category"] for r in final)), "total", len(final))
print("journal DOIs found:", sum(1 for r in final if r["category"] == "journal" and r["doi"]))
print("journal DOI NOT_FOUND:", sum(1 for r in final if r["category"] == "journal" and not r["doi"]))
