# Transpiedecuesta — official route map source

Source: https://transpiedecuesta.com/transporte-de-pasajeros/

The page's `mostrarRuta()` function maps route variants to separate outbound (`ida`) and inbound (`regreso`) JPG URLs. These are **raster images**, not GIS data.

Run `python scripts/scrape_transpiedecuesta.py` or the **Scrape Transpiedecuesta route maps** GitHub Action.

Outputs:
- `routes.json`: route labels and original image URLs
- `report.json`: HTTP statuses, fallback URLs, image validation, SHA-256 hashes
- `images/`: successfully downloaded source images
- `source_page.html`: captured HTML evidence

The scraper tries the published URL first and then the `-scaled`/unscaled WordPress alternative. It does not fabricate route shapes, stop locations, schedules, or frequency data. A 404 remains documented in the report. Image availability must be checked by running the workflow.
