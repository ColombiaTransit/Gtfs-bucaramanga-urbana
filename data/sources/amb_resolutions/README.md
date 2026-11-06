# AMB resolutions scraper

Official archives: https://www.amb.gov.co/resoluciones-transporte-metropolitano/ and https://www.amb.gov.co/resoluciones-secretaria-general-2026/

The scraper discovers linked AMB resolution archives, inventories listed resolutions, tries published download links, validates PDFs, calculates SHA-256, and extracts embedded PDF text. It runs **selective Spanish OCR** only on PDF pages with insufficient embedded text (fewer than 60 non-whitespace characters). Other pages retain their embedded text. It does not infer legal validity, routes, or frequencies.

Run the **Scrape AMB resolutions** workflow manually with `max_documents=0` (all) and `max_archives=24` (archive page limit). Weekly updates are configured.

Outputs committed to Git: `manifest.json`, `index.csv`. PDF originals and text files are available in the 90-day workflow artifact `amb-resolutions-archive`, not committed as binaries. `page_results` records extraction method, OCR attempts and remaining unreadable pages. `needs_ocr` flags documents still requiring manual review after selective OCR. Original PDFs remain unchanged. Use `--no-ocr` to disable OCR.

**First-run validation required:** the AMB site may use WordPress download-manager links that need an additional adapter. Missing links, HTTP failures and non-PDF responses are recorded rather than silently assumed successful. The archive limit and public navigation determine coverage; 'all' refers to documents discovered within that scope.
