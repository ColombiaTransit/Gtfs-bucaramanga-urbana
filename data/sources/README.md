# Bucaramanga urban transit — source register

This directory records source datasets for the future GTFS feed. Historical route listings are **not** evidence of current operation.

## Sources

| ID | Origin | Source | Status |
|---|---|---|---|
| bucaramanga-2020-2021 | datos.gov.co, dataset `5syf-tgsx` | Operator/route records, distance, capacity and historical monthly observations | Downloadable via workflow; not verified as current service |
| unitransa-route-map | https://rutas.unitransa.com/mapa_rutas.php | UNITRANSA route map, route names, lengths and reported GPS-point counts | Web snapshot; GPS geometry still to be extracted |

The source MHT capture supplied during research is not automatically recoverable from the public website; it must be retained separately if original archived bytes are required.

Run the **Fetch Bucaramanga source data** GitHub Action to archive HTTP responses and the Socrata JSON dataset. Review downloaded data before using them in GTFS.

Do not infer route frequencies from capacity_minima/capacidad_maxima or historical monthly fields. Route names shared across companies must not be duplicated as separate GTFS services without route-variant verification.
