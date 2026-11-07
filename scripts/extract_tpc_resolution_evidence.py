#!/usr/bin/env python3
"""Review AMB archived text and update the single shared evidence register.
Candidate mentions are not treated as verified operational facts.
"""
import argparse, csv, json, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REGISTER=Path("data/registers/transport_source_evidence.csv")
MANIFEST=Path("data/sources/amb_resolutions/manifest.json")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--archive",default="data/sources/amb_resolutions")
    args=ap.parse_args()
    archive=Path(args.archive)
    manifest=json.loads(MANIFEST.read_text(encoding="utf-8"))
    docs={(str(d.get("resolution_year")),str(d.get("resolution_number"))):d for d in manifest["documents"]}
    with REGISTER.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f); fields=reader.fieldnames; rows=list(reader)
    def extract_one(row):
        doc=docs.get((row["year"],row["source_id"]))
        if not doc:
            return {"record_id":row["record_id"],"status":"missing_manifest","candidate_pages":[]}
        sha=doc.get("download",{}).get("sha256")
        source=archive/"text"/(str(sha)+".txt")
        if not sha or not source.exists():
            return {"record_id":row["record_id"],"status":"missing_text","candidate_pages":[]}
        raw=source.read_text(encoding="utf-8",errors="replace")
        sections=re.split(r"(?=--- Page \d+ \([^)]*\) ---)",raw)
        patterns={"route":r"\b(?:ruta|recorrido|itinerario|trayecto)s?\b",
                  "frequency":r"\b(?:frecuencia|intervalo)s?\b",
                  "hours":r"\b(?:horario|primer\s+despacho|ultimo\s+despacho|último\s+despacho)s?\b",
                  "legal":r"\b(?:modifica|deroga|revoca|sustituye|vigencia)\b"}
        pages=[]
        extracts=[]
        for section in sections:
            match=re.search(r"--- Page (\d+)",section)
            if not match:continue
            page=int(match.group(1))
            hits=[kind for kind,pattern in patterns.items() if re.search(pattern,section,re.I)]
            if not hits:continue
            pages.append({"page":page,"topics":hits})
            lines=section.splitlines()
            keep=set()
            for i,line in enumerate(lines):
                if any(re.search(p,line,re.I) for p in patterns.values()):
                    keep.update(range(max(0,i-3),min(len(lines),i+5)))
            extracts.append({"page":page,"topics":hits,
                             "excerpts":"\n".join(lines[i] for i in sorted(keep))[:18000],
                             "source_page_chars":len(section)})
        dest=Path("data/sources/amb_resolutions/evidence")
        dest.mkdir(parents=True,exist_ok=True)
        filename=dest/(row["record_id"]+".json")
        filename.write_text(json.dumps({
            "source_resolution":row["source_id"]+"-2026",
            "record_id":row["record_id"],"source_url":row["source_url"],
            "source_sha256":sha,"excerpts":extracts,
            "note":"Unverified extracted source text; no inferred operational claims"
        },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return {"record_id":row["record_id"],"status":"indexed",
                "text_chars":len(raw),"candidate_pages":pages,"excerpt_file":str(filename)}
    targets=[r for r in rows if r["source_type"]=="operating_resolution" and r["year"]=="2026"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        report=list(pool.map(extract_one,targets))
    # Preserve all existing human-reviewed status and values in the central register.
    out=Path("data/registers/amb_extraction_review.json")
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Indexed",sum(x["status"]=="indexed" for x in report),"of",len(report),"documents; manual verification still required")
if __name__=="__main__":main()
