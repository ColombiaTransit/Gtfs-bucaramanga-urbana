# AMB TPC stop-data research — 2026-11-07

## Confirmed official leads (not yet downloaded/validated as stop datasets)

1. **AMB 2023 stop-characterisation/location study.** The AMB 2023 fourth-quarter management report states that the transport subdirectorate delivered a study on characterisation and location of public-transport stops to Bucaramanga's transit authority on **25 August 2023**, with an attached report. The same report mentions an assessment of existing stops in Floridablanca. Source: https://www.bucaramanga.gov.co/wp-content/uploads/2024/04/informe-de-gestion-cuarto-trimestre-vigencia-2023-amb.pdf . **Next:** locate the study and any annexes or coordinate tables; do not mistake a narrative mention for downloaded geodata.

2. **PMM cartographic archive.** AMB's Plan Maestro de Movilidad page lists **ANEXO 05. ARCHIVOS CARTOGRAFICOS** (approx. 268 MB) for Bucaramanga. Source: https://www.amb.gov.co/actualizacion-plan-maestro-de-movilidad/ . **Next:** inspect the ZIP and inventory point layers (paradero/parada/TPC/SITM), fields, CRS, dates, geometry and coverage before using anything in GTFS.

3. **Official route baseline.** The current AMB TPC route page documents 45 routes, but no verified stop sequence is established from it. Source: https://www.amb.gov.co/rutas-publico-colectivo-complementario/ .

## Data-quality and GTFS policy

- Keep official AMB stop points separate from OSM candidates and SITM stations. Never silently treat all SITM stops as TPC stops.
- Spatially match candidate stops to the archived AMB KML route geometries, inspect direction and access, and report confidence and unmatched routes.
- A mapped point near a route is not proof that a bus may stop there.
- Do not generate arbitrary evenly spaced stops or stop_times.
- Do not assume hail-and-ride along all 45 routes or generate GTFS-Flex continuous pickup/drop-off without evidence that boarding/alighting outside fixed stops is permitted.
- Retain source URLs, dates, coordinate reference system, attribution and confidence for each candidate stop.

## Status

Research leads identified; no authoritative machine-readable stop inventory has yet been verified or ingested. Next task is obtaining and examining the PMM cartographic annex and the 2023 stop study.
