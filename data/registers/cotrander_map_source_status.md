# COTRANDER TPC — Google My Maps geometry source status

Recorded: 2026-11-06

## Evidence and scope

- Official operator website: https://www.cotrander.com/
- Published TPC routes: https://www.cotrander.com/rutas/rutas-tpc
- The TPC route page includes embedded Google Maps / My Maps iframes.
- The project maintainer observed the following message when opening a map: **"Unavailable — This map is no longer available due to a violation of our Terms of Service and/or policies."**
- This is evidence that the **observed map** is unavailable; it does **not** establish that every iframe or all six route maps are unavailable.
- Two map identifiers were previously observed (route-to-ID mapping should be rechecked against page HTML before reuse): `1lL8ArWDzJrVpQBpoea40YT0EellACZ4` (26 Cumbre), `1kdyA7qrSrcQ3N4PvzmNObDdeiuLxeUQ` (07 Limoncito).

## Data disposition

| Data | Status | GTFS implication |
|---|---|---|
| Six route names and codes | Recorded in `data/sources/cotrander_tpc_routes.csv` | Candidate `routes.txt` entries; validate variants and operator relationships |
| Distance, duration, frequency ranges | Recorded from operator page | Preserve as published source data; not yet an exact timetable |
| Embedded My Maps geometry | Unavailable for the map showing the policy message; other maps not individually verified | No reliable shape extracted; do not mark a route as having a shape based on iframe presence |
| Alternative route geometry | Not yet sourced | Search authoritative GIS/OSM/other operator route traces later |

## Research decision

Do not build a KML extraction workflow targeting a map known to display the policy-unavailable message. Retain iframe/map IDs as provenance, not as usable geometries. If another iframe is individually confirmed accessible, evaluate it separately. Do not infer `shapes.txt` coordinates or route direction from the unavailable map.

The published frequency ranges remain distinct from validated GTFS `frequencies.txt` service periods.
