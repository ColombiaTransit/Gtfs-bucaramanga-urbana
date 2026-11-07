# Visually verified resolution frequency differences (2026-11-07)

The following values were visually checked by a human reviewer against the original PDF page images rendered from the archived, SHA-256-indexed AMB resolutions (GitHub Actions run 42352631877; artifact 13566500655). They are **verified source readings**, not automatically adopted GTFS values.

| Resolution | PDF page (1-based) | Route | Peak interval (min) | Off-peak interval (min) | Verification |
| --- | ---: | ---: | ---: | ---: | --- |
| AMB-2026-000078 | 8 | 43 | 5 | 15 | Human-confirmed against original page |
| AMB-2026-000082 | 9 | 45 | 5 | 15 | Human-confirmed against original page |
| AMB-2026-000092 | 15 | 50 | 8 | 9 | Human-confirmed against original page |

## Source precedence and next steps

The official AMB TPC route publication remains the operational baseline for the GTFS under [source-precedence-amb-tpc.md](source-precedence-amb-tpc.md). The resolution readings differ from the current AMB route listing: route 43 (AMB 8/10), route 45 (AMB peak 10), route 50 (AMB 6/8). Preserve both readings with their provenance. Do **not** silently replace published operational headways or treat a table excerpt as proof of current legal applicability; investigate effective dates, table context and supersession separately when needed.

Original rendered pages are available in the workflow artifact [amb-three-original-table-pages](https://github.com/ColombiaTransit/Gtfs-bucaramanga-urbana/actions/runs/42352631877/artifacts/13566500655).
