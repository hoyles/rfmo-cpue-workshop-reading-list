import json, re, sys, warnings
import os
from pathlib import Path
warnings.filterwarnings("ignore")
from pypdf import PdfReader

ROOT = Path(os.environ.get("CPUE_SRC", "."))   # set CPUE_SRC to the source collection
OUT = ROOT / "oa-check-output"
rows = json.load(open(OUT / "_stage1.json", encoding="utf-8"))

DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"'<>,;)\]]+", re.I)

def clean(d):
    d = d.rstrip(".,;:)]}>'\"")
    d = re.sub(r"\.pdf$", "", d, flags=re.I)
    return d

def page_text(p, n=2):
    try:
        r = PdfReader(str(p))
        meta = dict(r.metadata or {})
        txts = []
        for i in range(min(n, len(r.pages))):
            try: txts.append(r.pages[i].extract_text() or "")
            except Exception: txts.append("")
        return meta, txts, len(r.pages), None
    except Exception as e:
        return {}, [], 0, repr(e)

want = {"journal", "uncertain", "rfmo_verify"}
res = {}
for row in rows:
    if row["category"] not in want: continue
    p = ROOT / row["relative_path"]
    meta, txts, npages, err = page_text(p, 2)
    full = "\n".join(txts)
    doi, src, ctx = "", "none", ""
    # 2. embedded metadata
    for k, v in meta.items():
        if v and isinstance(v, str):
            m = DOI_RE.search(v)
            if m and ("doi" in k.lower() or "10." in v):
                doi, src, ctx = clean(m.group(0)), "pdf_metadata", f"{k}={v[:120]}"
                break
    # 3. first two pages of text
    if not doi:
        m = DOI_RE.search(full)
        if m:
            doi, src = clean(m.group(0)), "page_text"
            s = max(0, m.start()-90); ctx = full[s:m.end()+40].replace("\n", " ")
    res[row["relative_path"]] = {
        "doi": doi, "doi_source": src, "ctx": ctx, "npages": npages, "err": err,
        "has_text": bool(full.strip()),
        "meta_title": str(meta.get("/Title", ""))[:150],
        "p1": re.sub(r"\s+", " ", txts[0])[:1400] if txts else "",
        "docite": bool(re.search(r"(do not cite|not to be cited|without .{0,30}permission|working paper.{0,80}not.{0,20}cite)", full, re.I)),
        "docite_ctx": (lambda m: full[max(0,m.start()-200):m.end()+200].replace("\n"," ") if m else "")(
            re.search(r"(do not cite|not to be cited|without .{0,30}permission)", full, re.I)),
    }
json.dump(res, open(OUT / "_stage2.json", "w", encoding="utf-8"), indent=1)
print("extracted:", len(res))
print("no text layer:", sum(1 for v in res.values() if not v["has_text"]))
print("errors:", sum(1 for v in res.values() if v["err"]))
