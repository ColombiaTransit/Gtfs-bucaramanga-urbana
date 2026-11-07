# Transport evidence register

Use **one** shared register: `data/registers/transport_source_evidence.csv` for all investigations (AMB resolutions, operator websites, route maps, schedules, OCR reviews and future GTFS source reconciliation). Do not create separate investigation-specific review CSV files.

## Fields
- `record_id`: stable unique key (e.g. `AMB-2026-000071`).
- `source_type`: operating_resolution, route_map, operator_website, schedule, etc.
- `source_id`, `year`, `operator`, `source_url`: source identity.
- `download_status`, `ocr_flag`: acquisition and readability metadata, **not** verification of route facts.
- `content_review_status`: pending_pdf_content_review, reviewed, partially_reviewed, or blocked.
- `route_codes`, `headways`, `service_hours`, `legal_supersession`: populate only with supported findings. Empty means **not yet established**, not absence.
- `evidence_reference`: document page/table/paragraph and, when relevant, artifact path.
- `review_notes`: uncertainties, contradictions, next action.

## Review rules
1. Inspect archived PDF extracted text first; only rerun OCR on demonstrably unreadable pages.
2. Cite document and page for every operational finding; distinguish explicit source claims from interpretation.
3. Keep historical information even if superseded; document relationships instead of silently replacing records.
4. Compare overlapping operator routes before generating GTFS trips or frequencies.
5. Preserve one row per source document in the initial inventory; for multiple conflicting findings, add uniquely identified evidence rows to this **same** register, never a new per-study register.
6. An `ocr_flag=false` does not mean the PDF's tables were fully checked.

## Current queue
Prioritize 2026 AMB resolutions 000071 (COTRANDER), 000072 (Transportes Colombia), 000073 (UNITRANSA), then the remaining ten. Their PDF originals and extracted text are in the `amb-resolutions-archive` GitHub Actions artifact from run 42295672543; `manifest.json` and `index.csv` are the acquisition inventory. Extract route/frequency facts only after reviewing that content.
