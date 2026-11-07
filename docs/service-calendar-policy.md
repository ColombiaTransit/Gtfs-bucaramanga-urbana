# TPC Bucaramanga — GTFS service calendar and holiday policy

Status: **approved modelling assumptions** (2026-11-07). These are not verified AMB operating rules.

## Service-day classification

- Monday–Friday, excluding Colombian public holidays: weekday service.
  - Peak: 07:00–09:00 and 17:00–20:00 (local time, America/Bogota).
  - Off-peak: all other operating hours.
- Saturday, excluding Colombian public holidays: Saturday service, **no peak windows**; use the applicable off-peak/Saturday frequency.
- Sunday: Sunday service, no peak windows.
- **Any Colombian public holiday, including a holiday falling on Saturday or a weekday: Sunday service**. Holiday precedence overrides the ordinary weekday/Saturday classification.

Use the Python `holidays` package (`holidays.country_holidays("CO", years=...)`) to determine observed Colombian public holidays, including Monday transfers under the Emiliani rules. Do **not** hardcode dates or infer holidays solely from weekday. Evaluate each GTFS service date in the local Colombian calendar (America/Bogota), not UTC.

When generating GTFS `calendar_dates.txt`, remove holiday dates from the applicable ordinary weekday/Saturday service and add them to the Sunday-equivalent service. Avoid duplicate contradictory exceptions and avoid adding a holiday twice if it already falls on Sunday. If the generator instead assigns service IDs by individual dates, use the same classification function and ensure only the intended service is active.

Keep route-specific first/last departures and published frequency data as authoritative inputs. Do not invent weekend frequency values: missing Saturday/Sunday/holiday frequency data must be flagged for review, with any fallback explicitly identified as a modelling assumption.

## Route model

- Preserve the 45 published AMB routes and their existing KML-based shapes.
- Model *parada libre* as an **unverified assumption**.
- Prefer GTFS `continuous_pickup=0` and `continuous_drop_off=0` on eligible routes, rather than automatically generating Flex polygons.
- A shape alone is insufficient for a complete GTFS trip: each trip still needs valid stop_times and endpoint stops.
- OSM bus stops are candidate reference locations only, not verified TPC stops.

## Implementation

The Python helper `scripts/colombia_service_calendar.py` implements date classification. The GTFS generator must call it when building service calendars and exceptions. **Adding this helper does not itself wire it into the existing generator.**
