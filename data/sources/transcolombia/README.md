# TRANSCOLOMBIA route-map source

Official website: https://transcolombia.com.co/

The website's Next.js route list maps ten public route codes to PAX codes.
The interactive map loads JSON from `/api/pax/route/{paxCode}`.
The response is expected to contain `success`, `geometry` (longitude,
latitude pairs), `stops` (latitude, longitude, sequence, neighbourhood), and
possibly `name`. These fields are verified from the website JavaScript;
actual API payloads must still be checked by the workflow.

Run manually via **Scrape TRANSCOLOMBIA Routes**, or locally:

```sh
python scripts/scrape_transcolombia.py
```

Outputs: `raw/*.json` (original API evidence), `routes.geojson`,
`route_stops.csv`, and `summary.json`.

V15 and CP24 have no PAX code on the website and are deliberately excluded
from requests, not from the operator route register. Route stops are not
deduplicated or assumed to be GTFS stop IDs. A valid geometry requires at
least two coordinate pairs. The scraper does not invent frequency or
operating hours. Route P8 must be compared with UNITRANSA and COTRANDER
before combining any operator services.
