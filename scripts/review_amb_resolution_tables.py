#!/usr/bin/env python3
"""Conservative, read-only review of resolutions against authoritative AMB-published route data.

AMB-published operating values are the default GTFS baseline; legal discrepancies are flagged. Missing or OCR-damaged numeric cells
are queued for visual inspection only on the specific page.
"""
import csv,json,re,unicodedata
from pathlib import Path
from collections import Counter

BASE=Path("data")
OUT=BASE/"reports"/"amb_resolution_table_review"
OUT.mkdir(parents=True,exist_ok=True)
routes=json.loads((BASE/"sources/amb_tpc_routes/routes.json").read_text(encoding="utf-8"))
with (BASE/"registers/transport_source_evidence.csv").open(encoding="utf-8",newline="") as f:
    legal=[r for r in csv.DictReader(f) if r["source_type"]=="operating_resolution" and r["year"]=="2026"]
def norm(s):
    s=unicodedata.normalize("NFKD",s or "")
    return re.sub(r"[^A-Z0-9]","", "".join(c for c in s if not unicodedata.combining(c)).upper())
def code(s):
    s=str(s).strip()
    return str(int(s)) if s.isdigit() else s.upper()
def times(text):
    return re.findall(r"\b(?:0?[1-9]|1[0-2]):[0-5]\d(?::[0-5]\d)?\s*[AP]\s*\.?\s*M\.?",text,re.I)
def table_sections(text):
    # Restrict to table blocks starting with a route code and route label; avoid
    # accidental historical mentions and the many other 'CODIGO' tokens.
    lines=text.splitlines()
    starts=[i for i,l in enumerate(lines) if re.search(r"\bC[ÓO]DIGO\b",l,re.I)]
    for pos,i in enumerate(starts):
        segment="\n".join(lines[i:min(starts[pos+1] if pos+1<len(starts) else len(lines),i+90)])
        m=re.search(r"C[ÓO]DIGO\s*[:|]?\s*(\d{1,3}[A-Z]?)\b",segment,re.I)
        if m and re.search(r"\bRUTA\b",segment,re.I):
            yield code(m.group(1)),segment
review=[]
visual=[]
for e in legal:
    path=BASE/"sources/amb_resolutions/evidence"/(e["record_id"]+".json")
    if not path.exists():
        visual.append({"resolution":e["record_id"],"page":"","route_code":"","reason":"Missing extracted evidence file"})
        continue
    doc=json.loads(path.read_text(encoding="utf-8"))
    for page in doc["excerpts"]:
        p=page["page"]
        # The authorization table normally follows 'RESUELVE/ARTÍCULO PRIMERO'.
        # Other historical tables are retained as candidates but never assumed current.
        for route_code,segment in table_sections(page["excerpts"]):
            matches=[r for r in routes if code(r["route_code"])==route_code]
            own=[r for r in matches if norm(r["operator"])==norm(e["operator"]) or
                 norm(e["operator"]) in norm(r["operator"]) or norm(r["operator"]) in norm(e["operator"])]
            candidate=own[0] if len(own)==1 else None
            # Excerpt truncation and OCR order can merge neighboring tables.
            # Extract fields only if they appear on a single line with an unambiguous value.
            found={}
            for field,pat in {
                "frequency_peak_min":r"FRECUENCIA\s+PICO\s*\(min\.?\)\s*[:|]?\s*(\d{1,2})\b",
                "frequency_offpeak_min":r"FRECUENCIA\s+VALLE\s*\(min\.?\)\s*[:|]?\s*(\d{1,2})\b",
                "first_departure":r"PRIMER\s+DESPACHO\s*[:|]?\s*((?:0?[1-9]|1[0-2]):[0-5]\d(?::[0-5]\d)?\s*[AP]\s*M)",
                "last_departure":r"(?:ULTIMO|ÚLTIMO)\s+DESPACHO\s*[:|]?\s*((?:0?[1-9]|1[0-2]):[0-5]\d(?::[0-5]\d)?\s*[AP]\s*M)"
            }.items():
                m=re.search(pat,segment,re.I)
                if m:found[field]=m.group(1).strip()
            issues=[]
            if candidate:
                for field in ("frequency_peak_min","frequency_offpeak_min"):
                    if field in found and found[field]!=candidate[field]:
                        issues.append(field+": resolution="+found[field]+" AMB="+candidate[field])
            missing=[f for f in ("frequency_peak_min","frequency_offpeak_min","first_departure","last_departure") if f not in found]
            context="historical_or_current_unresolved"
            if re.search(r"ART[IÍ]CULO\s+PRIMERO|RESUELVE",page["excerpts"][:500],re.I):
                context="authorization_context_candidate"
            row={"resolution":e["record_id"],"page":p,"route_code":route_code,
                 "amb_route":candidate["route_name"] if candidate else "",
                 "amb_operator":candidate["operator"] if candidate else "",
                 "resolution_operator":e["operator"],"context":context,
                 "match_status":"operator_code_candidate" if candidate else ("code_only_other_operator" if matches else "code_not_in_amb"),
                 "extracted_fields":json.dumps(found,ensure_ascii=False),
                 "differences_to_review":"; ".join(issues),
                 "missing_or_unreadable_fields":";".join(missing),
                 "verification_status":"AMB_publication_authoritative_resolution_candidate_unverified"}
            review.append(row)
            if missing or issues:
                visual.append({"resolution":e["record_id"],"page":p,"route_code":route_code,
                               "reason":"missing_or_unreadable_cells" if missing else "potential_difference",
                               "fields":";".join(missing),"differences":"; ".join(issues)})
def write_csv(path,items,fields):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(items)
write_csv(OUT/"table_candidates.csv",review,["resolution","page","route_code","amb_route","amb_operator","resolution_operator","context","match_status","extracted_fields","differences_to_review","missing_or_unreadable_fields","verification_status"])
write_csv(OUT/"visual_review_queue.csv",visual,["resolution","page","route_code","reason","fields","differences"])
report={"resolution_count":len(legal),"amb_route_count":len(routes),
        "candidate_table_blocks":len(review),"candidate_match_statuses":dict(Counter(r["match_status"] for r in review)),
        "visual_review_queue":len(visual),
        "scope":"AMB-published routes, frequencies and departure windows are authoritative GTFS defaults. Resolution candidates are legal context; excerpts can omit cells or historical context.",
        "preservation":"No source register, verified evidence or GTFS modified."}
(OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
