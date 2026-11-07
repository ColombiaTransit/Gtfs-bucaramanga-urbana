#!/usr/bin/env python3
"""Extract and inspect two transport-related PDF maps from the official AMB RAR."""
import hashlib,json,re,subprocess
from pathlib import Path
import requests,fitz
URL="https://www.amb.gov.co/download/31486/"
SHA="a9df10ec16b2dfd124f0109700f67f10e2e05d4a4f76534fa171395c46eafe36"
NAMES=["P14C_BUC_CEstaciones.pdf","P14C_BUC_CTPúblico.pdf"]
out=Path("data/reports/amb_cartography_maps");out.mkdir(parents=True,exist_ok=True)
archive=Path("/tmp/amb_cartography.rar")
h=hashlib.sha256()
with requests.get(URL,stream=True,timeout=(30,180),headers={"User-Agent":"Mozilla/5.0"}) as r:
    r.raise_for_status()
    with archive.open("wb") as f:
        for chunk in r.iter_content(1024*1024):
            if chunk:
                h.update(chunk);f.write(chunk)
assert h.hexdigest()==SHA,"Source archive hash differs from verified download"
listing=subprocess.run(["7z","l","-slt",str(archive)],capture_output=True,text=True,check=True)
paths=[line[7:] for line in listing.stdout.splitlines() if line.startswith("Path = ")]
report={"source_url":URL,"source_sha256":SHA,"maps":[]}
for name in NAMES:
    matches=[p for p in paths if p.endswith("/"+name)]
    if len(matches)!=1:raise RuntimeError(f"Expected one {name}; found {matches}")
    data=subprocess.run(["7z","x","-so",str(archive),matches[0]],capture_output=True,check=True).stdout
    doc=fitz.open(stream=data,filetype="pdf")
    entry={"file":name,"pages":len(doc),"bytes":len(data),"pages_analysis":[]}
    for i,page in enumerate(doc):
        text=page.get_text("text")
        words=[line.strip() for line in text.splitlines() if re.search(r"parad|parader|estaci[oó]n|TPC|SITM|bus|transporte|rutas",line,re.I)]
        entry["pages_analysis"].append({"page":i+1,"page_width":page.rect.width,"page_height":page.rect.height,"text_characters":len(text),"transport_mentions":words[:70],"text_excerpt":text[:6000],"embedded_images":len(page.get_images()),"drawings":len(page.get_drawings())})
        if i<3:
            pix=page.get_pixmap(matrix=fitz.Matrix(1.7,1.7),alpha=False)
            pix.save(out/f"{name[:-4]}-page-{i+1}.png")
    report["maps"].append(entry)
(out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report,ensure_ascii=False,indent=2)[:18000])
