# Operator website register — Bucaramanga urban transit

This register records operator websites for eventual GTFS `agency.txt` creation. Entries are **candidates**, not automatically approved GTFS agencies.

| operator_key | operator_name | website | route_map_url | source | verification_status | agency_url_candidate | notes |
|---|---|---|---|---|---|---|---|
| unitransa | UNITRANSA S.A. | https://unitransa.com/ | https://rutas.unitransa.com/mapa_rutas.php | Operator homepage supplied by project maintainer; UNITRANSA route map scraped from inline `const RUTAS` | Homepage supplied by maintainer; route-map source confirmed | https://unitransa.com/ | Use the homepage for `agency_url`; retain the route-map subdomain separately as a GTFS data source. |
| cotrander | COTRANDER | https://www.cotrander.com/ | https://www.cotrander.com/rutas/rutas-tpc ; https://www.cotrander.com/rutas/rutas-en-convenio | Operator homepage supplied by project maintainer | Homepage and TPC route page identified | https://www.cotrander.com/ | Use as the candidate `agency_url`; TPC route page lists six routes; convenio page lists five complementary routes, all with duration, distance and frequency. P8 and P14 require cross-operator variant matching with UNITRANSA before GTFS deduplication. User reports Google My Maps iframe error: 'Unavailable — This map is no longer available due to a violation of our Terms of Service and/or policies.' Treat affected maps as unavailable for shape extraction; do not assume all six are blocked. See `data/registers/cotrander_map_source_status.md` for map availability evidence and GTFS disposition. Confirm formal operator name and route assignments before generating `agency.txt`. |

| transcolombia | TRANSCOLOMBIA | https://transcolombia.com.co/ | | Operator homepage supplied by project maintainer | Homepage supplied by maintainer; route sources not yet assessed | https://transcolombia.com.co/ | Candidate `agency_url`; verify legal name, route inventory and operator assignments before GTFS generation. |

| lusitania | Transportes Lusitania | https://transporteslusitania.com/ | https://transporteslusitania.com/index.php/about/ | Official operator route images | Website and four timetable images checked; current validity unverified | https://transporteslusitania.com/ | Images include Rionegro and Playón services; check TPC scope before GTFS inclusion. |

## GTFS mapping policy

- `agency_name`: use the confirmed public operator name.
- `agency_url`: use the operator's homepage (UNITRANSA: `https://unitransa.com/`; COTRANDER: `https://www.cotrander.com/`; TRANSCOLOMBIA: `https://transcolombia.com.co/`).
- `agency_timezone`: `America/Bogota`.
- `agency_id`: assign a stable identifier when the operator-to-route relationships have been validated.
- Do not create duplicate agencies or trips for jointly operated route variants; shared services may require a composite agency and `attributions.txt`.
- A website alone does not verify `agency_lang`, contact details, or operator assignments.

Last recorded: 2026-11-06.
