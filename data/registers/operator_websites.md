# Operator website register — Bucaramanga urban transit

This register records operator websites for eventual GTFS `agency.txt` creation. Entries are **candidates**, not automatically approved GTFS agencies.

| operator_key | operator_name | website | route_map_url | source | verification_status | agency_url_candidate | notes |
|---|---|---|---|---|---|---|---|
| unitransa | UNITRANSA S.A. | https://unitransa.com/ | https://rutas.unitransa.com/mapa_rutas.php | Operator homepage supplied by project maintainer; UNITRANSA route map scraped from inline `const RUTAS` | Homepage supplied by maintainer; route-map source confirmed | https://unitransa.com/ | Use the homepage for `agency_url`; retain the route-map subdomain separately as a GTFS data source. |
| cotrander | COTRANDER | https://www.cotrander.com/ | https://www.cotrander.com/rutas/rutas-tpc | Operator homepage supplied by project maintainer | Homepage and TPC route page identified | https://www.cotrander.com/ | Use as the candidate `agency_url`; TPC route page lists six routes with duration, distance and frequency; confirm formal operator name and route assignments before generating `agency.txt`. |

## GTFS mapping policy

- `agency_name`: use the confirmed public operator name.
- `agency_url`: use the operator's homepage (UNITRANSA: `https://unitransa.com/`; COTRANDER: `https://www.cotrander.com/`).
- `agency_timezone`: `America/Bogota`.
- `agency_id`: assign a stable identifier when the operator-to-route relationships have been validated.
- Do not create duplicate agencies or trips for jointly operated route variants; shared services may require a composite agency and `attributions.txt`.
- A website alone does not verify `agency_lang`, contact details, or operator assignments.

Last recorded: 2026-11-06.
