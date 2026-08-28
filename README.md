# Reading list — Global Joint Tuna RFMO Longline CPUE Technical Workshop

Reference material for the workshop in **Yokohama, 12–16 October 2026**.

Several participants have no institutional library access, so this repository
answers one question for every item on the list: **where can you legally get a
free copy?**

**→ [`reading-list.md`](reading-list.md)** is the list. Start there.

## What is and is not here

This repository is mostly **links, not files**. That is deliberate:

- **RFMO documents** (ICCAT, IATTC, IOTC, WCPFC/SPC, ISC, CCSBT) are free to
  download from the organisation that issued them. They are listed with their
  document identifiers rather than mirrored, so each organisation stays the
  publisher of its own document and you always get the current version.
- **Journal articles** are listed by DOI, with a free link where one exists.
- **Only four PDFs are committed**, in [`pdfs/`](pdfs/). Each carries a
  Creative Commons Attribution licence, which permits redistribution with
  attribution. See [`pdfs/ATTRIBUTION.md`](pdfs/ATTRIBUTION.md) for the citation
  and licence of each.

Nothing paywalled is redistributed here, and nothing is mirrored that its
publisher has not licensed for redistribution.

## The underlying audit

[`data/oa_check.csv`](data/oa_check.csv) is the full record — one row per file
examined, 208 rows:

| column | meaning |
|---|---|
| `relative_path` | path in the source collection |
| `category` | `rfmo_public`, `rfmo_verify`, `journal`, `uncertain`, `duplicate`, `excluded` |
| `doi`, `doi_source` | DOI and where it came from: `ris`, `pdf_metadata`, `page_text`, `none` |
| `is_oa`, `oa_status`, `best_free_url` | from the Unpaywall API |
| `notes` | licence statements, document identifiers, restrictions, duplicate links |

[`data/oa_check_summary.txt`](data/oa_check_summary.txt) has the counts, the
items needing a human decision, and the method notes.

| category | n | |
|---|---|---|
| `rfmo_public` | 100 | free from the issuing organisation |
| `rfmo_verify` | 51 | needs a permissions check before circulation |
| `journal` | 13 | 5 free, 8 paywalled |
| `uncertain` | 3 | unresolved from the file alone |
| `duplicate` | 38 | same document held more than once |
| `excluded` | 3 | not a reference item, or out of scope |

## Three things to know before circulating anything

1. **17 ISC Shark Working Group papers carry a notice on page 1**: *"Working
   document submitted to the ISC … Document not to be cited without author's
   permission."* Get author permission first. No ALBWG, BILLWG or PBFWG paper
   carries such a notice — every document was scanned in full, not just page 1.
2. **CCSBT ESC papers** carry no restriction notice, but CCSBT may limit them to
   members. Confirm with the CCSBT Secretariat.
3. **Eight journal articles have no free version.** They need an author-supplied
   accepted manuscript, an Elsevier Share Link, or a DOI link with a note that
   access varies. All eight are in *Fisheries Research*.

## Reproducing the audit

[`scripts/`](scripts/) holds the pipeline, in order:

| script | does |
|---|---|
| `oa_check.py` | classifies every file by path and filename |
| `oa_extract.py` | pulls DOIs — PDF metadata, then first two pages — and scans for citation notices |
| `oa_assemble.py` | applies content-based reclassifications, resolves duplicates by MD5, writes the CSV |
| `oa_unpaywall.py` | queries Unpaywall for each DOI |
| `oa_summary.py` | writes the plain-text summary |
| `make_repo.py` | builds this repository |

```bash
export CPUE_SRC=/path/to/the/collection
python scripts/oa_check.py
python scripts/oa_extract.py
python scripts/oa_assemble.py
python scripts/oa_unpaywall.py you@example.org
python scripts/make_repo.py
```

Needs Python 3 and `pypdf`. `CPUE_SRC` points at the source collection, which is
not public — the scripts are here so the method is inspectable, not so they can
be re-run as-is. Unpaywall requires an email as a URL parameter; pass your own.

Rules the pipeline follows: no DOI is ever guessed or inferred from a filename;
duplicates are established by hashing file contents, not by comparing filenames;
no full-text PDF is downloaded; and the source collection is never modified.

## Licence

The compiled list, the audit data and the scripts are released under
[CC0 1.0](LICENSE) — use them however you like, no attribution needed.

This does **not** extend to the PDFs in [`pdfs/`](pdfs/). Those remain under
their publishers' CC BY licences and must be attributed to their authors; cite
the original article, never this repository.

## Corrections and additions

Open an issue. Particularly useful: a free version of one of the eight
paywalled articles, a resolution for anything in the `uncertain` category, or a
document identifier that does not resolve at its organisation's portal.
