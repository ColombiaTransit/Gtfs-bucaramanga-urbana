#!/usr/bin/env python3
"""Archive official Transpiedecuesta route maps and report missing images.

The site embeds static JPG links in mostrarRuta(); no geometry is inferred.
"""
import argparse
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PAGE = "https://transpiedecuesta.com/transporte-de-pasajeros/"
BASE = Path("data/sources/transpiedecuesta")
USER_AGENT = "ColombiaTransit-GTFS-Research/1.0 (public source archival)"
PAIR_RE = re.compile(r'["\'](?P<key>ruta[\w-]+)["\']\s*:\s*\{\s*ida\s*:\s*["\'](?P<ida>https?[^"\']+)["\']\s*,\s*regreso\s*:\s*["\'](?P<regreso>https?[^"\']+)["\']', re.I | re.S)
OPTION_RE = re.compile(r'<option\s+value=["\'](?P<key>ruta[\w-]+)["\']\s*>(?P<label>.*?)</option>', re.I | re.S)

def get(url):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "image/*,text/html;q=0.8,*/*;q=0.5"})
    with urlopen(req, timeout=35) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read(), response.geturl()

def candidates(url):
    yield url
    if "-scaled." in url:
        yield url.replace("-scaled.", ".")
    else:
        stem, ext = url.rsplit(".", 1)
        yield stem + "-scaled." + ext

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(BASE))
    args = parser.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    page_status, _, page_data, _ = get(PAGE)
    source = html.unescape(page_data.decode("utf-8", errors="replace"))
    (out / "source_page.html").write_text(source, encoding="utf-8")
    labels = {m.group("key"): re.sub("<[^>]+>", "", m.group("label")).strip() for m in OPTION_RE.finditer(source)}
    pairs = list(PAIR_RE.finditer(source))
    if not pairs:
        raise RuntimeError("No route image pairs found; website markup may have changed")
    images = out / "images"
    images.mkdir(exist_ok=True)
    results = []
    for match in pairs:
        key = match.group("key")
        for direction in ("ida", "regreso"):
            original = match.group(direction)
            attempts = []
            saved = None
            for url in dict.fromkeys(candidates(original)):
                try:
                    status, content_type, payload, resolved = get(url)
                    valid = payload[:3] == b"\xff\xd8\xff" or payload[:8] == b"\x89PNG\r\n\x1a\n"
                    attempts.append({"url": url, "status": status, "content_type": content_type, "valid_image": valid})
                    if status == 200 and valid:
                        ext = ".png" if payload.startswith(b"\x89PNG") else ".jpg"
                        path = images / (key + "-" + direction + ext)
                        path.write_bytes(payload)
                        saved = {"path": str(path), "url": resolved, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
                        break
                except HTTPError as e:
                    attempts.append({"url": url, "status": e.code, "error": str(e.reason)})
                except (URLError, TimeoutError, OSError) as e:
                    attempts.append({"url": url, "status": None, "error": str(e)})
                time.sleep(0.2)
            results.append({"route_variant": key, "label": labels.get(key, key), "direction": direction, "source_url": original, "attempts": attempts, "download": saved})
            print(f"{key} {direction}: {'OK' if saved else 'MISSING'}")
    report = {"source_page": PAGE, "checked_at_utc": datetime.now(timezone.utc).isoformat(), "page_http_status": page_status, "route_variants": len(pairs), "image_count": len(results), "downloaded": sum(bool(x["download"]) for x in results), "images": results}
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "routes.json").write_text(json.dumps([{"key": m.group("key"), "label": labels.get(m.group("key"), m.group("key")), "ida_url": m.group("ida"), "regreso_url": m.group("regreso")} for m in pairs], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Downloaded {report['downloaded']}/{len(results)} route maps. See {out / 'report.json'}")
    if report["downloaded"] == 0:
        print("WARNING: No images available; retaining route metadata and HTTP diagnostics.")

if __name__ == "__main__":
    main()
