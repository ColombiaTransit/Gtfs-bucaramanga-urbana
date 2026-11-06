#!/usr/bin/env python3
"""Fetch public TRANSCOLOMBIA route maps and export GTFS research inputs."""
import argparse
import csv
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://transcolombia.com.co/api/pax/route/"
ROUTES = [
    ("CE24", "R24L"), ("CEP24", "R24P"), ("CH15", "R15"),
    ("CI17", "R17"), ("NC21", "NC21"), ("R23", "R23"),
    ("V14", "V14"), ("AN3", "AN3"), ("P19", "P19"), ("P8", "P8"),
]

def valid_coordinate(lon, lat):
    return (isinstance(lon, (int, float)) and not isinstance(lon, bool)
            and isinstance(lat, (int, float)) and not isinstance(lat, bool)
            and math.isfinite(lon) and math.isfinite(lat)
            and -180 <= lon <= 180 and -90 <= lat <= 90)

def fetch(code, retries=3):
    url = BASE + urllib.parse.quote(code, safe="")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "ColombiaTransit-GTFS-research/1.0",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=35) as response:
                data = response.read(20_000_000)
            return json.loads(data.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt == retries - 1:
                raise RuntimeError(str(exc)) from exc
            time.sleep(2 ** attempt)

def run(output):
    output.mkdir(parents=True, exist_ok=True)
    raw = output / "raw"
    raw.mkdir(exist_ok=True)
    features, stop_rows, results = [], [], []
    for public_code, pax_code in ROUTES:
        result = {"route_code": public_code, "pax_code": pax_code,
                  "source_url": BASE + pax_code, "status": "error",
                  "geometry_points": 0, "stops": 0, "invalid_points": 0}
        try:
            payload = fetch(pax_code)
            (raw / (public_code + ".json")).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if not isinstance(payload, dict) or payload.get("success") is not True:
                result["status"] = "api_unsuccessful"
                results.append(result)
                continue
            coordinates = []
            geometry = payload.get("geometry") or []
            if not isinstance(geometry, list):
                geometry = []
            for point in geometry:
                if (isinstance(point, (list, tuple)) and len(point) >= 2
                        and valid_coordinate(point[0], point[1])):
                    coordinates.append([point[0], point[1]])
                else:
                    result["invalid_points"] += 1
            result["geometry_points"] = len(coordinates)
            if len(coordinates) >= 2:
                features.append({"type": "Feature",
                    "properties": {"route_code": public_code, "pax_code": pax_code,
                                   "source_url": BASE + pax_code,
                                   "route_name": payload.get("name")},
                    "geometry": {"type": "LineString", "coordinates": coordinates}})
            stops = payload.get("stops") or []
            if not isinstance(stops, list):
                stops = []
            for stop in stops:
                if not isinstance(stop, dict):
                    continue
                lat, lon = stop.get("lat"), stop.get("lon")
                if not valid_coordinate(lon, lat):
                    continue
                stop_rows.append({"route_code": public_code, "pax_code": pax_code,
                    "seq": stop.get("seq", ""), "lat": lat, "lon": lon,
                    "barrio": stop.get("barrio") or "",
                    "source_url": BASE + pax_code})
                result["stops"] += 1
            result["status"] = "ok" if len(coordinates) >= 2 else (
                "stops_only" if result["stops"] else "no_usable_geometry_or_stops")
        except Exception as exc:
            result["error"] = str(exc)
        results.append(result)
        print(f"{public_code}: {result['status']}, geometry={result['geometry_points']}, stops={result['stops']}")
    (output / "routes.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = ["route_code", "pax_code", "seq", "lat", "lon", "barrio", "source_url"]
    with (output / "route_stops.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(stop_rows)
    report = {"source": BASE, "routes_requested": len(ROUTES),
              "routes_with_geometry": len(features), "stop_records": len(stop_rows),
              "excluded_no_pax_code": ["V15", "CP24"], "routes": results}
    (output / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if any(r["status"] in ("ok", "stops_only") for r in results) else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/sources/transcolombia")
    args = parser.parse_args()
    raise SystemExit(run(Path(args.output)))
