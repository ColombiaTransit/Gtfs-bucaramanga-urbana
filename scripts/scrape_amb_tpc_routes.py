#!/usr/bin/env python3
"""Archive official AMB TPC routes, timetable fields and Google Maps links."""
import csv, json, re, hashlib, argparse
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup

URL = "https://www.amb.gov.co/rutas-publico-colectivo-complementario/"
FIELDS = ["route_code","route_name","operator","terminal","cartel_ida","cartel_regreso","recorrido","length_km","capacity_max","capacity_min","frequency_peak_min","frequency_offpeak_min","frequency_low_demand_min","first_departure","first_departure_low_demand","last_departure","last_departure_low_demand","service_level","vehicle_class","map_url","map_id","source_url"]
LABELS = {"CÓDIGO":"route_code","RUTA":"route_name","EMPRESA":"operator","TERMINAL":"terminal","CARTEL DE RUTA IDA":"cartel_ida","CARTEL DE RUTA REGRESO":"cartel_regreso","RECORRIDO":"recorrido","LONGITUD (KMS.)":"length_km","CAP. MÁXIMA":"capacity_max","CAP. MÍNIMA":"capacity_min","FRECUENCIA PICO":"frequency_peak_min","FRECUENCIA VALLE":"frequency_offpeak_min","PRIMER DESPACHO":"first_departure","ULTIMO DESPACHO":"last_departure","ÚLTIMO DESPACHO":"last_departure","NIVEL DE SERVICIO":"service_level","CLASE":"vehicle_class"}
def clean(s): return re.sub(r"\s+"," ",s or "").strip()
def map_id(url):
    p=urlparse(url); q=parse_qs(p.query)
    return (q.get("mid") or q.get("id") or [""])[0]
def parse(raw):
    soup=BeautifulSoup(raw,"html.parser")
    routes=[]
    last_iframe=""
    for node in soup.find_all(["iframe","table"]):
        if node.name=="iframe":
            last_iframe=node.get("src","")
            continue
        row={k:"" for k in FIELDS}
        for tr in node.find_all("tr"):
            cells=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["td","th"],recursive=False)]
            if len(cells)<2:
                continue
            label=cells[0].upper().rstrip(":")
            field=LABELS.get(label)
            if label in ("CÓDIGO","CODIGO"):
                row["route_code"]=cells[1]
            elif field:
                row[field]=cells[1]
            if len(cells)>=4 and cells[2].upper().rstrip(":")=="BAJA DEMANDA":
                target={"FRECUENCIA VALLE":"frequency_low_demand_min",
                        "PRIMER DESPACHO":"first_departure_low_demand",
                        "ULTIMO DESPACHO":"last_departure_low_demand",
                        "ÚLTIMO DESPACHO":"last_departure_low_demand"}.get(label)
                if target:row[target]=cells[3]
        if not row["route_code"] or not row["route_name"]:
            continue
        row["map_url"]=last_iframe
        row["map_id"]=map_id(last_iframe)
        row["source_url"]=URL
        routes.append(row)
        last_iframe=""
    return routes
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="data/sources/amb_tpc_routes");ap.add_argument("--html");args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    if args.html:raw=Path(args.html).read_bytes()
    else:
        with urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 ColombiaTransit/1.0"}),timeout=60) as response:raw=response.read()
    routes=parse(raw.decode("utf-8-sig",errors="replace"))
    if not routes:
        # Keep the actual runner response for diagnosing HTML layout or bot challenges.
        # Never overwrite the last successful route snapshot with empty data.
        (out/"failed_source_page.html").write_bytes(raw)
        soup=BeautifulSoup(raw,"html.parser")
        diagnostic={
            "source_url":URL,"response_bytes":len(raw),
            "title":clean(soup.title.get_text(" ",strip=True)) if soup.title else "",
            "route_heading_matches":len(soup.find_all(string=re.compile(r"RUTA\\s*#\\s*\\d+",re.I))),
            "table_count":len(soup.find_all("table")),
            "iframe_count":len(soup.find_all("iframe")),
            "body_preview":clean(soup.get_text(" ",strip=True))[:1200],
        }
        (out/"failure_diagnostics.json").write_text(json.dumps(diagnostic,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
        print(json.dumps(diagnostic,ensure_ascii=False,indent=2))
        raise RuntimeError("No routes parsed; raw runner HTML archived for diagnosis")
    (out/"source_page.html").write_bytes(raw)
    (out/"routes.json").write_text(json.dumps(routes,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"routes.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(routes)
    report={"source_url":URL,"checked_at_utc":datetime.now(timezone.utc).isoformat(),"source_sha256":hashlib.sha256(raw).hexdigest(),"route_count":len(routes),"map_count":sum(bool(x["map_url"]) for x in routes),"operators":sorted(set(x["operator"] for x in routes if x["operator"])),"incomplete_routes":[x["route_code"] for x in routes if not x["operator"] or not x["map_url"]]}
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
