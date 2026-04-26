# Changelog

All notable changes to MPF (Memory Portability Format) are documented here.

The format follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
- **major** — incompatible spec changes; consumers must understand the new version
- **minor** — additive, forward-compatible changes (new optional fields, new
  sidecar kinds); v0.1.x consumers must skip unknown additions cleanly
- **patch** — clarifications to spec text, schema bug fixes that don't change
  the wire shape

## [0.1.1] — 2026-04-26

Initial public spec release. Extracted from MNEMOS as the canonical home for
the format independent of any single implementation.

### Records
- `kind: "memory"` with `payload_version: "mnemos-3.1"` (extensible — peers
  may declare their own payload versions)
- Other kinds (`document`, `fact`, `event`) reserved by spec, currently emitted
  only by upstream sources (docling, etc.)

### Sidecars
- `kg_triples` — knowledge graph triples linked to memory records
- `memory_versions` — git-like DAG of memory edits (parent_version_id chain)
- `compression_manifest` — provenance for compressed memory variants

### Tooling
- JSON Schema (draft 2020-12) at `schema/mpf-v0.1.json`
- Standalone validator at `validate.py`
- Three canonical test vectors at `vectors/`

## Pre-release history

The format originated inside MNEMOS as `tools/memory_export.py` and
`tools/memory_import.py` (v3.2 line). Its versioned schema first
appeared in MNEMOS commit history under `docs/mpf_v0.1.json`. v0.1.0
of the standalone spec corresponds to MNEMOS v3.4.0.
