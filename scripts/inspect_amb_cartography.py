#!/usr/bin/env python3
"""Inspect AMB cartographic annex without committing the large source archive."""
import json, os, re, sys, zipfile, hashlib, subprocess
from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

PAGE="https://www.amb.gov.co/actualizacion-plan-maestro-de-movilidad/"
out=Path("data/reports/amb_cartography_inventory");out.mkdir(parents=True,exist_ok=True)
session=requests.Session();session.headers["User-Agent"]="Mozilla/5.0 (compatible; ColombiaTransit research)"
report={"page":PAGE,"target":"ANEXO 05. ARCHIVOS CARTOGRAFICOS","status":"not_started"}
try:
    resp=session.get(PAGE,timeout=60);resp.raise_for_status()
    soup=BeautifulSoup(resp.text,"html.parser")
    matches=soup.find_all(string=lambda t: bool(t and "ANEXO 05. ARCHIVOS CARTOGRAFICOS" in t.upper()))
    report["matching_labels"]=len(matches)
    candidates=[]
    for match in matches:
        for parent in list(match.parents)[:6]:
            if parent.name in ("tr","li","article","div"):
                for a in parent.find_all("a",href=True):
                    href=urljoin(PAGE,a["href"])
                    if href not in candidates:candidates.append(href)
                for el in parent.find_all(attrs={"data-url":True}):
                    href=urljoin(PAGE,el["data-url"])
                    if href not in candidates:candidates.append(href)
                if candidates:break
    report["candidate_urls"]=candidates[:20]
    # A download link must be explicitly associated with the matching label.
    valid=[u for u in candidates if re.search(r"/download/\d+|\.zip(?:\?|$)|\.rar(?:\?|$)|\.7z(?:\?|$)",u,re.I)]
    if not valid:
        report["status"]="download_link_not_resolved"
    else:
        url=valid[0];report["download_url"]=url
        with session.get(url,stream=True,timeout=(30,180),allow_redirects=True) as r:
            r.raise_for_status()
            report["content_type"]=r.headers.get("Content-Type")
            limit=600*1024*1024
            path=Path("/tmp/amb_cartography_download")
            size=0;sha=hashlib.sha256()
            with path.open("wb") as f:
                for chunk in r.iter_content(1024*1024):
                    if not chunk:continue
                    size+=len(chunk)
                    if size>limit:raise ValueError("Download exceeds 600 MiB safety limit")
                    sha.update(chunk);f.write(chunk)
        report.update(download_bytes=size,sha256=sha.hexdigest())
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z:
                members=[{"name":i.filename,"bytes":i.file_size,"compressed_bytes":i.compress_size} for i in z.infolist() if not i.is_dir()]
            report["members"]=members
            report["stop_candidates"]=[m for m in members if re.search(r"parad|parader|estacion|station|stop|transporte|tpc",m["name"],re.I)]
            report["status"]="zip_inventoried"
        elif path.open("rb").read(8).startswith(b"Rar!"):
            proc=subprocess.run(["7z","l","-slt",str(path)],capture_output=True,text=True,timeout=180)
            if proc.returncode:
                raise RuntimeError("7z list failed: "+proc.stderr[-1500:])
            entries=[]
            for block in proc.stdout.split("\n\n"):
                fields={}
                for line in block.splitlines():
                    if " = " in line:
                        k,v=line.split(" = ",1)
                        fields[k]=v
                if fields.get("Path") and fields.get("Size") and fields.get("Folder")!="+":
                    entries.append({"name":fields["Path"],"bytes":int(fields["Size"])})
            report["members"]=entries
            report["stop_candidates"]=[m for m in entries if re.search(r"parad|parader|estacion|station|stop|transporte|tpc",m["name"],re.I)]
            report["status"]="rar_inventoried"
        else:
            report["status"]="downloaded_unknown_format"
except Exception as exc:
    report["status"]="error";report["error"]=str(exc)
(out/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="members"},ensure_ascii=False,indent=2)[:8000])
if report["status"] in ("error","download_link_not_resolved"):sys.exit(1)
