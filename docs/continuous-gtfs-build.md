# Continuous-stop GTFS build — input contract

This is an initial implementation. It does **not** automatically extract the existing 45 AMB KML routes or legal frequency register. Before running, prepare the authoritative route manifest and one KML per route variant.

Required paths:
- `data/gtfs_routes.csv`: UTF-8 CSV with headers below.
- `data/kml/`: KML files referenced by relative filename in the CSV.

CSV header:

```csv
route_id,route_short_name,route_long_name,kml_file,first_departure,last_departure,duration_minutes,weekday_peak_minutes,weekday_offpeak_minutes,saturday_minutes,sunday_minutes
```

Every route needs validated values. The build intentionally **fails** on missing times, headways, or ambiguous multi-LineString KML files rather than inventing values. For routes with multiple directions, each variant needs a separate manifest row and KML. No example coordinates or placeholder frequency numbers should be committed as production inputs.

The generator creates:
- `agency.txt`, `routes.txt`, `stops.txt`, `trips.txt`, `stop_times.txt`, `shapes.txt`, `calendar_dates.txt`, `frequencies.txt`
- Route-level continuous pickup and drop-off.
- Provisional start/end stops at the first and last KML coordinates. These must be reviewed; a closed-loop KML may need a distinct end stop and direction-aware trip representation.
- Explicit daily service IDs so Colombian public holidays receive Sunday service.
- Weekday peaks 07:00–09:00 and 17:00–20:00; Saturdays are entirely off-peak; Sundays and holidays use Sunday frequency.

`duration_minutes` is **not** inferred from KML geometry; it must be sourced or explicitly approved as an estimate. The current builder uses `exact_times=0`, meaning headway-based service.

Run locally:

```bash
python -m pip install "holidays>=0.60,<1"
python scripts/build_continuous_gtfs.py --manifest data/gtfs_routes.csv --kml-dir data/kml --output dist/gtfs.zip --start-date 2026-11-07 --days 365
```

The workflow `Build and validate Bucaramanga GTFS` invokes the MobilityData GTFS Schedule Validator after generation and uploads the feed and validation report as artifacts. **The workflow has not yet been successfully run against the 45-route production manifest.** A successful validator run must be verified before publishing.

Next integration tasks: map the existing AMB source register and KML archive into the manifest; verify route direction, trip duration, holiday service semantics and validator notices; do not silently synthesize missing legal schedule data.

## AMB source integration (2026-11-07)

The workflow now prepares `dist/gtfs_routes.csv` automatically using `scripts/prepare_amb_gtfs.py`, reading the **existing** committed `data/sources/amb_tpc_routes/routes.csv` and `kml_manifest.json`, and the 45 corresponding KML files under `data/sources/amb_tpc_routes/kml/`. No new scraping or manual copying is required.

**Explicit provisional modelling choices:** the AMB `frequency_low_demand_min` and `first_departure_low_demand` / `last_departure_low_demand` fields are used for Saturday, Sunday and public holidays. The published peak/off-peak headways and standard service hours are used for ordinary weekdays. Trip duration is estimated from AMB route length at 18 km/h, rounded up, with a minimum of 10 minutes. These values are **not official travel times** and must be reviewed before publication. The converter fails on missing/invalid data and checks route-to-KML matching. The MobilityData validator is invoked after the build; successful completion has not yet been verified.

Run locally:

```bash
python scripts/prepare_amb_gtfs.py --source data/sources/amb_tpc_routes --output dist/gtfs_routes.csv
python scripts/build_continuous_gtfs.py --manifest dist/gtfs_routes.csv --kml-dir data/sources/amb_tpc_routes --output dist/gtfs.zip --days 365
```
