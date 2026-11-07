#!/usr/bin/env python3
"""Adapt the committed AMB route register and KML manifest for the GTFS builder.

No network scraping. Missing data and mismatches are reported and fail the build.
Travel duration is explicitly ESTIMATED from published length at 18 km/h;
this is a provisional model assumption, not an AMB timetable.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from datetime import datetime

FIELDS = ("route_id", "route_short_name", "route_long_name", "kml_file",
          "first_departure", "last_departure", "first_departure_low_demand",
          "last_departure_low_demand", "duration_minutes",
          "weekday_peak_minutes", "weekday_offpeak_minutes",
          "saturday_minutes", "sunday_minutes")


def convert_time(raw):
    raw = str(raw).strip()
    if not raw:
        raise ValueError("missing departure time")
    for pattern in ("%I:%M:%S %p", "%I:%M %p", "%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(raw, pattern).strftime("%H:%M:%S")
        except ValueError:
            continue
    raise ValueError(f"unsupported time: {raw!r}")


def positive_int(raw, field, code):
    try:
        val = float(str(raw).replace(",", "."))
        if val <= 0 or not val.is_integer():
            raise ValueError()
        return int(val)
    except ValueError:
        raise ValueError(f"route {code}: missing/invalid {field}: {raw!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/sources/amb_tpc_routes"))
    parser.add_argument("--output", type=Path, default=Path("dist/gtfs_routes.csv"))
    parser.add_argument("--speed-kmh", type=float, default=18.0)
    args = parser.parse_args()
    if not 5 <= args.speed_kmh <= 50:
        parser.error("--speed-kmh must be between 5 and 50")
    with (args.source / "routes.csv").open(encoding="utf-8-sig", newline="") as file:
        source_rows = list(csv.DictReader(file))
    manifest_text = (args.source / "kml_manifest.json").read_text(encoding="utf-8")
    # Source scraper currently appends a literal backslash-n after the JSON array.
    # Tolerate that known trailing artifact, but reject any other trailing data.
    manifest_text = manifest_text.rstrip()
    if manifest_text.endswith(chr(92) + "n"):
        manifest_text = manifest_text[:-2].rstrip()
    manifest = json.loads(manifest_text)
    by_code = {str(item["route_code"]).strip(): item for item in manifest}
    if len(by_code) != len(manifest):
        raise ValueError("duplicate KML route codes")
    output = []
    for row in source_rows:
        code = str(row["route_code"]).strip()
        item = by_code.get(code)
        if not item or item.get("status") != "downloaded" or int(item.get("linestrings", 0)) != 1:
            raise ValueError(f"route {code}: no unambiguous downloaded KML")
        kml = item["kml_file"]
        if not (args.source / kml).is_file():
            raise ValueError(f"route {code}: missing {kml}")
        length = float(row["length_km"].replace(",", "."))
        if length <= 0:
            raise ValueError(f"route {code}: missing route length")
        duration = max(10, math.ceil(length / args.speed_kmh * 60))
        peak = positive_int(row["frequency_peak_min"], "frequency_peak_min", code)
        offpeak = positive_int(row["frequency_offpeak_min"], "frequency_offpeak_min", code)
        low = positive_int(row["frequency_low_demand_min"], "frequency_low_demand_min", code)
        output.append(dict(route_id="AMB_"+code, route_short_name=code,
            route_long_name=row["route_name"], kml_file=kml,
            first_departure=convert_time(row["first_departure"]),
            last_departure=convert_time(row["last_departure"]),
            first_departure_low_demand=convert_time(row["first_departure_low_demand"]),
            last_departure_low_demand=convert_time(row["last_departure_low_demand"]),
            duration_minutes=duration, weekday_peak_minutes=peak,
            weekday_offpeak_minutes=offpeak, saturday_minutes=low,
            sunday_minutes=low))
    if len(output) != len(by_code):
        raise ValueError(f"source mismatch: {len(output)} route rows, {len(by_code)} KMLs")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    print(f"Mapped {len(output)} AMB routes to {args.output}")
    print("MODEL ASSUMPTIONS: Saturday/Sunday use AMB low-demand headway and hours;")
    print(f"travel durations estimated at {args.speed_kmh:g} km/h. Review before publication.")


if __name__ == "__main__":
    main()
