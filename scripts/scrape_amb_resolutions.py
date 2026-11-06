#!/usr/bin/env python3
"""Archive public AMB resolutions, retaining source evidence and OCR backlog."""
import argparse, csv, hashlib, json, re, time, unicodedata
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

ROOT="https://www.amb.gov.co"
SEEDS=[ROOT+"/resoluciones-transporte-metropolitano/",ROOT+"/resoluciones-secretaria-general-2026/"]
def norm(s): return unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower()
def allowed(s): return urlparse(s).hostname in ("www.amb.gov.co","amb.gov.co") and urlparse(s).scheme in ("http","https")
def fetch(s,u,**kw):
    for i in range(3):
        try:
            r=s.get(u,timeout=35,**kw)
            if r.status_code in (429,500,502,503,504) and i<2: time.sleep(2**i);continue
            return r
        except requests.RequestException:
            if i==2: raise
            time.sleep(2**i)
def candidates(row,base):
    found=[]
    for el in row.find_all(True):
        for attr in ("href","data-url","data-downloadurl","data-download-url","data-href"):
            v=el.get(attr,"")
            if not v or v.startswith(("javascript:","#","mailto:")): continue
            u=urljoin(base,v)
            if allowed(u) and u not in found: found.append(u)
        for v in re.findall(r"https?://[^\s\x22\x27)]+|/\?wpdmdl=\d+|/download/[^\s\x22\x27)]+",el.get("onclick","")):
            u=urljoin(base,v)
            if allowed(u) and u not in found: found.append(u)
    return found
def archives(s,limit):
    queue=list(SEEDS); result={}
    while queue and len(result)<limit:
        url=queue.pop(0)
        if url in result or not allowed(url):continue
        try:
            r=fetch(s,url); result[url]={"status":r.status_code,"html":r.text if r.ok else ""}
            if not r.ok:continue
            soup=BeautifulSoup(r.text,"html.parser")
            for a in soup.select("a[href]"):
                u=urljoin(url,a["href"]).split("#")[0];path=urlparse(u).path.lower()
                if allowed(u) and "resoluc" in path and not path.endswith((".pdf",".doc",".docx")) and u not in result and u not in queue and len(queue)<limit*4:queue.append(u)
        except requests.RequestException as e:result[url]={"status":None,"error":str(e),"html":""}
    return result
def records(url,html):
    soup=BeautifulSoup(html,"html.parser"); out=[]
    for row in soup.select("tr"):
        cells=row.find_all("td",recursive=False)
        if not cells:continue
        title=" ".join(cells[0].get_text(" ",strip=True).split())
        if "resoluc" not in norm(title):continue
        out.append({"title":title,"published_date":cells[1].get_text(" ",strip=True) if len(cells)>1 else "","archive_url":url,"download_candidates":candidates(row,url)})
    if not out:
        for a in soup.select("a[href]"):
            title=a.get_text(" ",strip=True);link=urljoin(url,a["href"])
            if "resoluc" in norm(title) and allowed(link) and (".pdf" in link.lower() or "wpdmdl=" in link):
                out.append({"title":title,"published_date":"","archive_url":url,"download_candidates":[link]})
    return out
def download(s,item,folder):
    attempts=[]
    for url in item["download_candidates"]:
        try:
            r=fetch(s,url,stream=True)
            if not r.ok:attempts.append({"url":url,"status":r.status_code});r.close();continue
            data=bytearray()
            for chunk in r.iter_content(65536):
                data.extend(chunk)
                if len(data)>35*1024*1024:break
            r.close()
            if len(data)>35*1024*1024:attempts.append({"url":url,"error":"size_limit"});continue
            if not data.startswith(b"%PDF-"):attempts.append({"url":url,"status":200,"error":"not_pdf"});continue
            sha=hashlib.sha256(data).hexdigest();path=folder/(sha+".pdf")
            if not path.exists():path.write_bytes(data)
            return {"status":"downloaded","source_url":url,"sha256":sha,"bytes":len(data),"pdf_file":str(path),"attempts":attempts}
        except requests.RequestException as e:attempts.append({"url":url,"error":str(e)})
    return {"status":"download_failed" if item["download_candidates"] else "no_download_link","attempts":attempts}
def extract(path,folder):
    try:
        import fitz
        with fitz.open(path) as doc:
            texts=[p.get_text("text",sort=True) for p in doc];pages=len(doc)
        content="\n\n".join(texts);target=folder/(Path(path).stem+".txt");target.write_text(content,encoding="utf-8")
        return {"pages":pages,"text_chars":len(content.strip()),"needs_ocr":len(content.strip())<max(100,pages*60),"text_file":str(target)}
    except Exception as e:return {"needs_ocr":True,"error":str(e)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--max-archives",type=int,default=24);ap.add_argument("--max-documents",type=int,default=0);ap.add_argument("--output",default="data/sources/amb_resolutions");args=ap.parse_args()
    root=Path(args.output);root.mkdir(parents=True,exist_ok=True);pdf=root/"pdf";txt=root/"text";pdf.mkdir(exist_ok=True);txt.mkdir(exist_ok=True)
    s=requests.Session();s.headers.update({"User-Agent":"ColombiaTransit-GTFS-Research/1.0","Accept":"text/html,application/pdf,*/*"})
    pages=archives(s,args.max_archives);items=[];seen=set()
    for url,page in pages.items():
        for item in records(url,page["html"]):
            key=(item["title"],tuple(item["download_candidates"]))
            if key in seen:continue
            seen.add(key);title=norm(item["title"]);num=re.search(r"resolucion\s*(?:no\.?|numero)?\s*0*(\d{1,6})\b",title);year=re.search(r"\b(20\d{2}|19\d{2})\b",title)
            item.update({"resolution_number":num.group(1).zfill(6) if num else "unknown","resolution_year":year.group(1) if year else "unknown","id":hashlib.sha256((url+item["title"]).encode()).hexdigest()[:16]});items.append(item)
    items.sort(key=lambda x:(x["resolution_year"],x["resolution_number"],x["title"]),reverse=True)
    for i,item in enumerate(items):
        if args.max_documents and i>=args.max_documents:item["download"]={"status":"not_attempted_limit"};continue
        item["download"]=download(s,item,pdf)
        if item["download"]["status"]=="downloaded":item["extraction"]=extract(item["download"]["pdf_file"],txt)
        if i%10==0:print("Processed",i+1,"/",len(items),flush=True)
    summary={"checked_at_utc":datetime.now(timezone.utc).isoformat(),"archives":[{"url":u,"status":v["status"],"error":v.get("error")} for u,v in pages.items()],"discovered":len(items),"downloaded":sum(x.get("download",{}).get("status")=="downloaded" for x in items),"needs_ocr":sum(x.get("extraction",{}).get("needs_ocr",False) for x in items),"no_download_link":sum(not x["download_candidates"] for x in items)}
    (root/"manifest.json").write_text(json.dumps({"summary":summary,"documents":items},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (root/"index.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["id","resolution_number","resolution_year","title","published_date","archive_url","download_status","source_url","sha256","needs_ocr"]);w.writeheader()
        for x in items:
            d=x.get("download",{});w.writerow({"id":x["id"],"resolution_number":x["resolution_number"],"resolution_year":x["resolution_year"],"title":x["title"],"published_date":x["published_date"],"archive_url":x["archive_url"],"download_status":d.get("status"),"source_url":d.get("source_url"),"sha256":d.get("sha256"),"needs_ocr":x.get("extraction",{}).get("needs_ocr")})
    print(json.dumps(summary,indent=2))
    if not items:raise SystemExit("No resolution entries discovered; inspect archive markup")
if __name__=="__main__":main()
