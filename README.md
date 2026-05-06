# MPF — Memory Portability Format

[![spec: v0.2.0](https://img.shields.io/badge/spec-v0.2.0-blue.svg)](MPF.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Think of it as the CSV export, but for agent memory.**

MPF is MNEMOS's memory portability format; standalone but informed by
W3C PROV and the lessons of MIF.

A schema-versioned JSON envelope for moving agent memory between
systems — and for snapshotting it as a portable backup. Like CSV,
MPF is:

- **Universal.** Any memory system can produce or consume it. MNEMOS,
  Mem0, Letta, Graphiti, Cognee, MemPalace, Zep, your-system-here.
- **Human-readable.** Open it in any text editor. Grep it. Diff it.
  Inspect it byte by byte if you have to.
- **Both interop AND backup.** Same file works for migrating between
  systems and for archiving a snapshot. Export to leave; export to
  protect; export to share; export to fork. One format, four reasons.
- **Honest about lossy fields.** System-specific extensions are
  documented, not hidden. If your data won't survive a round-trip,
  the spec tells you which fields and why.

It's a file-level format, not a wire protocol. The format is
intentionally compositional, neutral, and independently evolved at the
v0.2 line.

## What's in this repo

| Path | Purpose |
|---|---|
| [`MPF.md`](MPF.md) | The spec. Normative. Read this first. |
| [`schema/mpf-v0.2.json`](schema/mpf-v0.2.json) | JSON Schema (draft 2020-12) — current programmatic validation |
| [`schema/mpf-v0.1.json`](schema/mpf-v0.1.json) | JSON Schema for v0.1 backward compatibility |
| [`vectors/`](vectors/) | Canonical round-trip test fixtures every conformant implementation should accept |
| [`migrations/`](migrations/) | Offline best-effort adapters from other memory formats into MPF v0.2 |
| [`validate.py`](validate.py) | Standalone validator (single file, optional `jsonschema` dep) |
| [`pyproject.toml`](pyproject.toml) | Publishable as the `mpf` pip package |

## Status

**v0.2.0** — adds W3C PROV-DM-inspired record provenance, optional
bi-temporal tracking, v0.2 migration adapters, and conformance vectors
while retaining v0.1 schema compatibility. Forward-compatible:
implementations should skip unknown record kinds and unknown sidecar
fields.

The reference implementation is [MNEMOS](https://github.com/mnemos-os/mnemos),
which produces and consumes MPF via its CHARON module and `/v1/export` /
`/v1/import` endpoints. MNEMOS is not the only producer or consumer —
anyone can target the spec.

## Quick validate

```bash
pip install jsonschema
python validate.py --file vectors/memory_basic.json
python validate.py vectors/
# → OK
```

## Adopting MPF in your memory system

If you maintain a memory system and want MPF support:

1. **Read [`MPF.md`](MPF.md)** — the field reference.
2. **Map your shape to `payload_version`** — declare your own (e.g.
   `mem0-1.x`), or target `mnemos-3.1` if your model fits.
3. **Round-trip the test vectors** — your import + export of `vectors/*.json`
   should preserve all fields. Unknown sidecars (`kg_triples`,
   `memory_versions`, `deletion_log`, `compression_manifest`) skip cleanly
   if you don't support them.
4. **Validate before shipping** — run `python validate.py --file <yours>`.

## Discussion

Spec-level / cross-system interop conversation lives at
[github.com/mnemos-os/mnemos/discussions](https://github.com/mnemos-os/mnemos/discussions)
under the **"the gods bring gifts"** master thread. File issues on this
repo for spec ambiguities, schema bugs, or vector-validation regressions.

## Roadmap

- **v0.1.x** — memories + KG triples + memory-versions DAG
  + compression manifest sidecars
- **v0.2** — current: PROV-DM-inspired provenance, optional bi-temporal
  fields, deletion-log schema surface, migration adapters, conformance vectors
- **v1.0** — locked spec, governance handoff candidate (LF AI & Data, etc.)

## License

[MIT](LICENSE).

The spec text, JSON Schema, validator, and test vectors are all under
the same MIT license — chosen to maximize adoption across memory
systems regardless of their own license. Implementations targeting
MPF can use any license.

(Note: the reference implementation, [MNEMOS](https://github.com/mnemos-os/mnemos),
is Apache 2.0. MIT for the spec, Apache 2.0 for the impl is intentional —
the spec stays maximally adoptable, the impl carries patent grants for
its enterprise users.)
