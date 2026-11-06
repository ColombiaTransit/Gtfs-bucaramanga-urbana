#!/usr/bin/env python3
"""Extract UNITRANSA's inline const RUTAS without executing webpage JavaScript."""
import argparse
import json
import re
from pathlib import Path

import json5


def extract_array(source):
    marker = re.search(r"\b(?:const|let|var)\s+RUTAS\s*=", source)
    if not marker:
        raise ValueError("RUTAS declaration not found in downloaded HTML")
    start = source.find("[", marker.end())
    if start < 0:
        raise ValueError("RUTAS array opening bracket missing")
    depth = 0
    quote = None
    escape = False
    comment = None
    for i in range(start, len(source)):
        c = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""
        if comment == "line":
            if c == "\n":
                comment = None
            continue
        if comment == "block":
            if c == "*" and nxt == "/":
                comment = None
            continue
        if quote:
            if escape:
                escape = False
            elif c == "\\":
                escape = True
            elif c == quote:
                quote = None
            continue
        if c == "/" and nxt == "/":
            comment = "line"
            continue
        if c == "/" and nxt == "*":
            comment = "block"
            continue
        if c in ('"', "'", "`"):
            quote = c
        elif c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return source[start:i + 1]
    raise ValueError("Unterminated RUTAS array")


def coordinate(p):
    if isinstance(p, dict):
        lat = p.get("lat", p.get("latitude"))
        lon = p.get("lng", p.get("lon", p.get("longitude")))
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return [lon, lat]
    if isinstance(p, (list, tuple)) and len(p) >= 2:
        a, b = p[:2]
        if all(isinstance(x, (int, float)) for x in (a, b)):
            # UNITRANSA/Leaflet typically uses [latitude, longitude].
            if 5 <= a <= 11 and -77 <= b <= -72:
                return [b, a]
            if -77 <= a <= -72 and 5 <= b <= 11:
                return [a, b]
    return None


def lines_from(value):
    if isinstance(value, list):
        direct = [coordinate(x) for x in value]
        if len(direct) >= 2 and all(direct):
            return [direct]
        result = []
        for item in value:
            result.extend(lines_from(item))
        return result
    if isinstance(value, dict):
        result = []
        for key in ("puntos", "points", "coordenadas", "coordinates", "coords", "recorrido", "trazado", "path", "latlngs", "geometry", "ruta"):
            if key in value:
                result.extend(lines_from(value[key]))
        return result
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", default="data/sources/unitransa")
    args = ap.parse_args()
    html = Path(args.html).read_text(encoding="utf-8", errors="replace")
    raw = extract_array(html)
    routes = json5.loads(raw)
    if not isinstance(routes, list) or not routes:
        raise ValueError("RUTAS is empty or not an array")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "rutas.json").write_text(json.dumps(routes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    features = []
    for i, route in enumerate(routes):
        lines = [line for line in lines_from(route) if len(line) >= 2]
        if not lines:
            continue
        props = {"source_index": i}
        if isinstance(route, dict):
            for key in ("id", "codigo", "code", "nombre", "name", "ruta"):
                if key in route and isinstance(route[key], (str, int, float)):
                    props[key] = route[key]
        geometry = {"type": "LineString", "coordinates": lines[0]} if len(lines) == 1 else {"type": "MultiLineString", "coordinates": lines}
        features.append({"type": "Feature", "properties": props, "geometry": geometry})
    (out / "rutas.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"routes": len(routes), "routes_with_geometry": len(features), "routes_without_geometry": len(routes) - len(features), "source": "https://rutas.unitransa.com/mapa_rutas.php"}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not features:
        print("WARNING: RUTAS extracted, but coordinate schema needs review before shapes.txt generation")


if __name__ == "__main__":
    main()
