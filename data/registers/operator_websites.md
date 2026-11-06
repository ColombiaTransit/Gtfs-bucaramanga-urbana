# Operator website register — Bucaramanga urban transit

This register records operator websites for eventual GTFS `agency.txt` creation. Entries are **candidates**, not automatically approved GTFS agencies.

| operator_key | operator_name | website | source | verification_status | agency_url_candidate | notes |
|---|---|---|---|---|---|---|
| unitransa | UNITRANSA S.A. | https://rutas.unitransa.com/mapa_rutas.php | UNITRANSA public route map, scraped from inline `const RUTAS` | Route-map source confirmed; corporate homepage not yet verified | https://rutas.unitransa.com/mapa_rutas.php | Operator-hosted route map. Use as provisional `agency_url` until the official corporate website is confirmed. |

## GTFS mapping policy

- `agency_name`: use the confirmed public operator name.
- `agency_url`: prefer the operator's verified official homepage; until verified, the working public route-map URL above is a provisional candidate.
- `agency_timezone`: `America/Bogota`.
- `agency_id`: assign a stable identifier when the operator-to-route relationships have been validated.
- Do not create duplicate agencies or trips for jointly operated route variants; shared services may require a composite agency and `attributions.txt`.
- The route-map source alone does not verify `agency_lang`, contact details, or all operator assignments.

Last recorded: 2026-11-06.
