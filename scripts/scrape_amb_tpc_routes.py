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
    soup=BeautifulSoup(raw,"html.parser"); routes=[]
    for heading in soup.find_all(re.compile(r"^h[1-6]$")):
        title=clean(heading.get_text(" ",strip=True))
        match=re.search(r"RUTA\s*#\s*([^\s]+)",title,re.I)
        if not match: continue
        row={k:"" for k in FIELDS}
        row["route_code"]=match.group(1)
        row["route_name"]=title[match.end():].strip()
        row["source_url"]=URL
        for node in heading.next_elements:
            if node is not heading and getattr(node,"name",None) and re.fullmatch(r"h[1-6]",node.name): break
            if getattr(node,"name",None)=="iframe":
                row["map_url"]=node.get("src","");row["map_id"]=map_id(row["map_url"])
            if getattr(node,"name",None)!="table":continue
            for tr in node.find_all("tr"):
                cells=[clean(x.get_text(" ",strip=True)) for x in tr.find_all(["td","th"],recursive=False)]
                for i in range(len(cells)-1):
                    label=cells[i].upper().rstrip(":")
                    field=LABELS.get(label)
                    if field:row[field]=cells[i+1]
                    if label=="BAJA DEMANDA" and i+1<len(cells):
                        if "FRECUENCIA VALLE" in [x.upper() for x in cells[:i]]:row["frequency_low_demand_min"]=cells[i+1]
                        elif "PRIMER DESPACHO" in [x.upper() for x in cells[:i]]:row["first_departure_low_demand"]=cells[i+1]
                        elif any("ULTIMO DESPACHO"==x.upper() or "ÚLTIMO DESPACHO"==x.upper() for x in cells[:i]):row["last_departure_low_demand"]=cells[i+1]
        routes.append(row)
    return routes
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",default="data/sources/amb_tpc_routes");ap.add_argument("--html");args=ap.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    if args.html:raw=Path(args.html).read_bytes()
    else:
        with urlopen(Request(URL,headers={"User-Agent":"Mozilla/5.0 ColombiaTransit/1.0"}),timeout=60) as response:raw=response.read()
    routes=parse(raw.decode("utf-8-sig",errors="replace"))
    if not routes:raise RuntimeError("No route headings found; refusing to overwrite previous snapshot")
    (out/"source_page.html").write_bytes(raw)
    (out/"routes.json").write_text(json.dumps(routes,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (out/"routes.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(routes)
    report={"source_url":URL,"checked_at_utc":datetime.now(timezone.utc).isoformat(),"source_sha256":hashlib.sha256(raw).hexdigest(),"route_count":len(routes),"map_count":sum(bool(x["map_url"]) for x in routes),"operators":sorted(set(x["operator"] for x in routes if x["operator"])),"incomplete_routes":[x["route_code"] for x in routes if not x["operator"] or not x["map_url"]]}
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
