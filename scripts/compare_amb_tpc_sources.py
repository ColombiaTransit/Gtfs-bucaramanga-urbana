#!/usr/bin/env python3
"""Non-destructive AMB catalogue reconciliation against registered operator and legal evidence."""
import csv
import json
import re
import unicodedata
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("data")
OUT = ROOT / "reports" / "amb_tpc_reconciliation"
OUT.mkdir(parents=True, exist_ok=True)

def read_csv(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def norm_code(s):
    s = str(s or "").strip().upper()
    if re.fullmatch(r"0+\d+", s):
        return str(int(s))
    return re.sub(r"\s+", " ", s)

def norm_operator(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).upper()
    return re.sub(r"[^A-Z0-9]+", "", s.replace("TRANSPORTES", "").replace("TRANSPORTE", "").replace("S.A.", "").replace("S.A", ""))

def clock(s):
    s = str(s or "").strip()
    if not s:
        return ""
    from datetime import datetime
    for fmt in ("%I:%M:%S %p", "%I:%M %p", "%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M")
        except ValueError:
            pass
    return s

routes = json.loads((ROOT / "sources/amb_tpc_routes/routes.json").read_text(encoding="utf-8"))
evidence = [r for r in read_csv(ROOT / "registers/transport_source_evidence.csv") if r.get("source_type") == "operating_resolution" and r.get("year") == "2026"]
operator_sources = [
    ("cotrander_tpc", ROOT / "sources/cotrander_tpc_routes.csv"),
    ("cotrander_convenio", ROOT / "sources/cotrander_convenio_routes.csv"),
]
operator_rows = [(label, r) for label, path in operator_sources for r in read_csv(path)]
by_code = {}
for label, r in operator_rows:
    by_code.setdefault(norm_code(r.get("route_code")), []).append((label, r))
legal_by_operator = {}
for e in evidence:
    legal_by_operator.setdefault(norm_operator(e["operator"]), []).append(e)
# The verified values below are transcribed from the existing evidence register,
# resolution 000071-2026, pp. 12 and 15. Do not extrapolate to other routes.
verified = {
    ("AMB-2026-000071", "7"): {"frequency_peak_min": "6", "frequency_offpeak_min": "10", "first_departure": "04:50", "last_departure": "20:30"},
    ("AMB-2026-000071", "36"): {"frequency_peak_min": "8", "frequency_offpeak_min": "12", "first_departure": "05:00", "last_departure": "19:30"},
}
rows = []
for route in routes:
    code = norm_code(route["route_code"])
    resolutions = legal_by_operator.get(norm_operator(route["operator"]), [])
    # Transportes Giron has multiple legal acts: retain all; do not assume supersession.
    issues = []
    references = []
    operator_matches = []
    for label, src in by_code.get(code, []):
        # Only compare a source with its corresponding operator.
        if label.startswith("cotrander") and norm_operator(route["operator"]) != norm_operator("COTRANDER"):
            continue
        operator_matches.append(label)
        lo, hi = src.get("frequency_min_minutes", ""), src.get("frequency_max_minutes", "")
        if lo and hi and label == "cotrander_tpc":
            for field, expected in [("frequency_peak_min", lo), ("frequency_offpeak_min", hi)]:
                if route[field] != expected:
                    issues.append(f"{field}: AMB={route[field]} operator={expected}")
        if src.get("route_name") and label == "cotrander_tpc":
            # Names may contain descriptions and accents; require human review, not automatic conflict.
            pass
    verified_count = 0
    for e in resolutions:
        fields = verified.get((e["record_id"], code))
        if not fields:
            continue
        references.append(e["record_id"])
        verified_count += 1
        for field, expected in fields.items():
            actual = clock(route[field]) if "departure" in field else route[field]
            if actual != expected:
                issues.append(f"{field}: AMB={actual} resolution={expected} ({e['record_id']})")
    if not resolutions:
        issues.append("No operator-matched resolution in the 13-record register")
    if issues:
        status = "review_required"
    elif verified_count:
        status = "verified_fields_agree"
    elif operator_matches:
        status = "operator_source_agrees_legal_pending"
    else:
        status = "legal_review_pending"
    rows.append({
        "route_code": route["route_code"], "route_name": route["route_name"],
        "amb_operator": route["operator"], "amb_peak": route["frequency_peak_min"],
        "amb_offpeak": route["frequency_offpeak_min"], "amb_low_demand": route["frequency_low_demand_min"],
        "amb_first": clock(route["first_departure"]), "amb_last": clock(route["last_departure"]),
        "operator_sources": ";".join(sorted(set(operator_matches))),
        "resolution_ids": ";".join(e["record_id"] for e in resolutions),
        "verified_resolution_fields": ";".join(references),
        "status": status, "differences": " | ".join(issues),
    })
with (OUT / "route_comparison.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
report = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "amb_route_count": len(rows),
    "registered_resolution_count": len(evidence),
    "status_counts": {s: sum(r["status"] == s for r in rows) for s in sorted(set(r["status"] for r in rows))},
    "resolution_review": [{"id": e["record_id"], "operator": e["operator"], "review_status": e["content_review_status"],
                           "mapped_amb_routes": [r["route_code"] for r in rows if e["record_id"] in r["resolution_ids"].split(";")]} for e in evidence],
    "notes": [
        "Only resolution 000071 route 7 and 36 fields are manually verified.",
        "All other resolution matches are operator-level associations, not route-level legal verification.",
        "No GTFS or source evidence registers are changed by this comparison.",
        "A shared route code across operators is not evidence of shared operation.",
        "Low-demand frequency and departure windows await legal verification.",
    ],
}
(OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
