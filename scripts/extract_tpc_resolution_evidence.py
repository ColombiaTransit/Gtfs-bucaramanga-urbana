#!/usr/bin/env python3
"""Review AMB archived text and update the single shared evidence register.
Candidate mentions are not treated as verified operational facts.
"""
import argparse, csv, json, re
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
    report=[]
    for row in rows:
        if row["source_type"]!="operating_resolution" or row["year"]!="2026":continue
        doc=docs.get((row["year"],row["source_id"]))
        if not doc:
            row["content_review_status"]="blocked"
            row["review_notes"]="Resolution not found in manifest"
            continue
        sha=doc.get("download",{}).get("sha256")
        text_path=archive/"text"/(str(sha)+".txt")
        if not sha or not text_path.exists():
            row["content_review_status"]="blocked"
            row["review_notes"]="Archived extracted text unavailable"
            continue
        content=text_path.read_text(encoding="utf-8",errors="replace")
        page_chunks=re.split(r"(?=--- Page \d+ \([^)]*\) ---)",content)
        evidence=[]
        for chunk in page_chunks:
            page=re.search(r"--- Page (\d+)",chunk)
            if not page:continue
            hits=[]
            for kind,pattern in [
                ("route",r"\b(?:ruta|recorrido|itinerario|trayecto)s?\b"),
                ("frequency",r"\b(?:frecuencia|intervalo)s?\b"),
                ("hours",r"\b(?:horario|primer\s+despacho|ultimo\s+despacho|último\s+despacho)s?\b"),
                ("legal",r"\b(?:modifica|deroga|revoca|sustituye|vigencia)\b")]:
                if re.search(pattern,chunk,re.I):hits.append(kind)
            if hits:evidence.append({"page":int(page.group(1)),"topics":hits})
        row["content_review_status"]="pending_manual_validation"
        row["evidence_reference"]="; ".join("p%d:%s"%(e["page"],"/".join(e["topics"])) for e in evidence)[:1500]
        row["review_notes"]="Automated keyword index only; no route/headway/hour claims verified. Text SHA256: "+sha
        report.append({"record_id":row["record_id"],"text_chars":len(content),"candidate_pages":evidence})
    with REGISTER.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    # Persist limited source excerpts for human verification, starting with COTRANDER.
    # Excerpts are evidence, not interpreted legal or schedule facts.
    priority=docs.get(("2026","000071"))
    if priority:
        sha=priority.get("download",{}).get("sha256")
        source=archive/"text"/(str(sha)+".txt")
        if source.exists():
            raw=source.read_text(encoding="utf-8",errors="replace")
            sections=re.split(r"(?=--- Page \\d+ \\([^)]*\\) ---)",raw)
            extracts=[]
            keywords=re.compile(r"frecuencia|intervalo|horario|despacho|ruta|recorrido|vigencia|modifica|deroga",re.I)
            for section in sections:
                page=re.search(r"--- Page (\\d+)",section)
                if not page:continue
                lines=section.splitlines()
                keep=set()
                for i,line in enumerate(lines):
                    if keywords.search(line):
                        keep.update(range(max(0,i-3),min(len(lines),i+5)))
                if keep:
                    extracts.append({"page":int(page.group(1)),"excerpts":"\\n".join(lines[i] for i in sorted(keep))[:18000]})
            dest=Path("data/registers/amb_cotrander_000071_evidence.json")
            dest.write_text(json.dumps({"source_resolution":"000071-2026","source_sha256":sha,"excerpts":extracts},ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
    out=Path("data/registers/amb_extraction_review.json")
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Indexed",len(report),"documents; manual verification still required")
if __name__=="__main__":main()
