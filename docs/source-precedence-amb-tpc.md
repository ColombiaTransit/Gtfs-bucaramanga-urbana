# Source precedence for Bucaramanga TPC GTFS

## Operational baseline

The official Área Metropolitana de Bucaramanga (AMB) route publication at
https://www.amb.gov.co/rutas-publico-colectivo-complementario/
is the authoritative **published operational baseline** for the current GTFS:
route codes, route names, operators, peak/off-peak/low-demand headways, and
first/last departures. Retain its source URL and snapshot.

## Legal evidence

The 13 registered AMB resolutions provide the legal basis, validity periods,
joint-operation arrangements, conditions, and possible supersession.
A published AMB value need not be manually revalidated against a resolution
before it can be used as the baseline. However, publication alone is not proof
that every legal provision is current. Flag explicit contradictions or unclear
supersession for human review; do not silently overwrite either source.

## Operator websites

Operator websites are secondary, potentially outdated sources. Record their
differences for provenance and investigation, but do **not** replace an AMB
published value based solely on an operator website.

## Research procedure

1. Preserve official AMB data as published; normalize only representation.
2. Compare resolutions for legal status, shared operation, and explicit
   operational conflicts, keeping page-level citations.
3. Prioritize unreadable cells only when they affect a concrete unresolved
   legal conflict or material GTFS decision. Do not bulk OCR all tables.
4. Keep verified legal evidence unchanged until a separately reviewed
   correction is justified.
5. Track operational source precedence separately from legal enforceability.
