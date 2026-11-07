#!/usr/bin/env python3
"""Build a conservative continuous-pickup GTFS feed from a route manifest and KMLs.

Manifest CSV columns:
route_id,route_short_name,route_long_name,kml_file,first_departure,last_departure,
duration_minutes,weekday_peak_minutes,weekday_offpeak_minutes,
saturday_minutes,sunday_minutes
Each KML must contain a LineString. Missing required data fails the build.
Times are local America/Bogota. Dates are service dates.
"""
import argparse
import csv
import io
import math
import sys
import zipfile
from datetime import date, datetime, timedelta, time
from pathlib import Path
from xml.etree import ElementTree as ET

from colombia_service_calendar import service_day_type

TABLES = {
    "agency.txt": ["agency_id", "agency_name", "agency_url", "agency_timezone"],
    "routes.txt": ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type", "continuous_pickup", "continuous_drop_off"],
    "stops.txt": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "trips.txt": ["route_id", "service_id", "trip_id", "shape_id"],
    "stop_times.txt": ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "shape_dist_traveled"],
    "shapes.txt": ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence", "shape_dist_traveled"],
    "calendar_dates.txt": ["service_id", "date", "exception_type"],
    "frequencies.txt": ["trip_id", "start_time", "end_time", "headway_secs", "exact_times"],
}
REQUIRED = ("route_id", "route_short_name", "kml_file", "first_departure",
            "last_departure", "duration_minutes", "weekday_peak_minutes",
            "weekday_offpeak_minutes", "saturday_minutes", "sunday_minutes")


def clock(value):
    parts = str(value).strip().split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"Invalid clock time: {value!r}")
    hh, mm = int(parts[0]), int(parts[1])
    ss = int(parts[2]) if len(parts) == 3 else 0
    if not (0 <= hh <= 47 and 0 <= mm < 60 and 0 <= ss < 60):
        raise ValueError(f"Invalid clock time: {value!r}")
    return hh * 3600 + mm * 60 + ss


def fmt(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def kml_points(path):
    root = ET.parse(path).getroot()
    candidates = []
    for elem in root.iter():
        if elem.tag.rsplit("}", 1)[-1] != "LineString":
            continue
        for child in elem.iter():
            if child.tag.rsplit("}", 1)[-1] == "coordinates" and child.text:
                pts = []
                for token in child.text.split():
                    p = token.split(",")
                    if len(p) >= 2:
                        lon, lat = float(p[0]), float(p[1])
                        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                            raise ValueError(f"Invalid coordinate in {path}")
                        pts.append((lat, lon))
                if len(pts) >= 2:
                    candidates.append(pts)
    if not candidates:
        raise ValueError(f"No LineString with >=2 points in {path}")
    # Do not concatenate unrelated variants or silently pick an arbitrary one.
    if len(candidates) != 1:
        raise ValueError(f"{path}: {len(candidates)} LineStrings; supply one KML per route variant")
    return candidates[0]


def meters(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    v = math.sin(dlat / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 12742000 * math.asin(min(1, math.sqrt(v)))


def intervals(row, day_type):
    if day_type in ("saturday", "sunday"):
        first = clock(row.get("first_departure_low_demand") or row["first_departure"])
        last = clock(row.get("last_departure_low_demand") or row["last_departure"])
    else:
        first, last = clock(row["first_departure"]), clock(row["last_departure"])
    if last <= first:
        last += 86400
    if day_type == "sunday":
        return [(first, last, int(row["sunday_minutes"]))]
    if day_type == "saturday":
        return [(first, last, int(row["saturday_minutes"]))]
    cuts = [first, last]
    for h in (7, 9, 17, 20):
        x = h * 3600
        if first < x < last:
            cuts.append(x)
    cuts = sorted(set(cuts))
    result = []
    for a, b in zip(cuts, cuts[1:]):
        mid = (a + b) / 2 % 86400
        peak = 7*3600 <= mid < 9*3600 or 17*3600 <= mid < 20*3600
        key = "weekday_peak_minutes" if peak else "weekday_offpeak_minutes"
        result.append((a, b, int(row[key])))
    return result


def write_feed(manifest, kml_dir, output, start, days):
    rows = list(csv.DictReader(open(manifest, encoding="utf-8-sig", newline="")))
    if not rows:
        raise ValueError("Route manifest is empty")
    data = {name: [] for name in TABLES}
    data["agency.txt"].append(dict(agency_id="AMB_TPC", agency_name="TPC Bucaramanga (AMB)",
                                   agency_url="https://www.amb.gov.co/", agency_timezone="America/Bogota"))
    seen = set()
    for row in rows:
        for key in REQUIRED:
            if not row.get(key, "").strip():
                raise ValueError(f"Route {row.get('route_id')}: missing {key}")
        rid = row["route_id"].strip()
        if rid in seen:
            raise ValueError(f"Duplicate route_id {rid}")
        seen.add(rid)
        duration = int(row["duration_minutes"])
        if duration <= 0 or any(int(row[k]) <= 0 for k in REQUIRED[-4:]):
            raise ValueError(f"{rid}: durations and headways must be positive")
        # Prevent path traversal in untrusted manifest.
        relative = Path(row["kml_file"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"{rid}: unsafe KML path")
        points = kml_points(kml_dir / relative)
        distances = [0.]
        for a, b in zip(points, points[1:]):
            distances.append(distances[-1] + meters(a, b))
        if distances[-1] < 10:
            raise ValueError(f"{rid}: route geometry is too short")
        shape_id = rid + "_shape"
        data["routes.txt"].append(dict(route_id=rid, agency_id="AMB_TPC",
            route_short_name=row["route_short_name"], route_long_name=row.get("route_long_name", ""),
            route_type=3, continuous_pickup=0, continuous_drop_off=0))
        for i, ((lat, lon), dist) in enumerate(zip(points, distances), 1):
            data["shapes.txt"].append(dict(shape_id=shape_id, shape_pt_lat=lat,
                shape_pt_lon=lon, shape_pt_sequence=i, shape_dist_traveled=round(dist / 1000, 3)))
        # Synthetic endpoints are explicitly placeholders; they must be reviewed.
        start_id, end_id = rid + "_START", rid + "_END"
        for sid, name, (lat, lon) in ((start_id, rid+" - Inicio (provisional)", points[0]),
                                       (end_id, rid+" - Fin (provisional)", points[-1])):
            data["stops.txt"].append(dict(stop_id=sid, stop_name=name, stop_lat=lat, stop_lon=lon))
        for typ in ("weekday", "saturday", "sunday"):
            sid = f"{rid}_{typ}"
            # Date-specific calendar: holiday precedence cannot overlap.
            for n in range(days):
                day = start + timedelta(days=n)
                if service_day_type(day) == typ:
                    data["calendar_dates.txt"].append(dict(service_id=sid, date=day.strftime("%Y%m%d"), exception_type=1))
            if not any(x["service_id"] == sid for x in data["calendar_dates.txt"]):
                continue
            windows = intervals(row, typ)
            for j, (a, b, headway) in enumerate(windows):
                if b <= a:
                    continue
                trip_id = f"{rid}_{typ}_{j}"
                data["trips.txt"].append(dict(route_id=rid, service_id=sid, trip_id=trip_id, shape_id=shape_id))
                for seq, stop, t, dist in ((1, start_id, a, 0), (2, end_id, a+duration*60, distances[-1]/1000)):
                    data["stop_times.txt"].append(dict(trip_id=trip_id, arrival_time=fmt(t),
                        departure_time=fmt(t), stop_id=stop, stop_sequence=seq,
                        shape_dist_traveled=round(dist, 3)))
                data["frequencies.txt"].append(dict(trip_id=trip_id, start_time=fmt(a),
                    end_time=fmt(b), headway_secs=headway*60, exact_times=0))
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, headers in TABLES.items():
            buf = io.StringIO(newline="")
            writer = csv.DictWriter(buf, fieldnames=headers, lineterminator="\n")
            writer.writeheader()
            writer.writerows(data[name])
            z.writestr(name, buf.getvalue())
    print(f"Created {output}: {len(rows)} routes, {len(data['trips.txt'])} frequency templates")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--kml-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("dist/gtfs.zip"))
    p.add_argument("--start-date", type=date.fromisoformat, default=date.today())
    p.add_argument("--days", type=int, default=365)
    args = p.parse_args()
    if not 1 <= args.days <= 730:
        p.error("--days must be 1..730")
    try:
        write_feed(args.manifest, args.kml_dir, args.output, args.start_date, args.days)
    except (ValueError, OSError, ET.ParseError) as exc:
        p.exit(1, f"GTFS build failed: {exc}\n")


if __name__ == "__main__":
    main()
