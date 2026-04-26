# MPF — Memory Portability Format

[![spec: v0.1.1](https://img.shields.io/badge/spec-v0.1.1-blue.svg)](MPF.md)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A schema-versioned JSON envelope for moving agent memory and parsed
documents between systems.**

MPF is the open contract that lets any RAG memory system — MNEMOS,
Mem0, Letta, Graphiti, Cognee, MemPalace, Zep, your-system-here — talk
to any other. It's a file-level format, not a wire protocol. Producers
emit MPF, consumers ingest MPF. The format is intentionally
compositional, neutral, and minimal at the v0.1 line.

## What's in this repo

| Path | Purpose |
|---|---|
| [`MPF.md`](MPF.md) | The spec. Normative. Read this first. |
| [`schema/mpf-v0.1.json`](schema/mpf-v0.1.json) | JSON Schema (draft 2020-12) — programmatic validation |
| [`vectors/`](vectors/) | Canonical round-trip test fixtures every conformant implementation should accept |
| [`validate.py`](validate.py) | Standalone validator (single file, optional `jsonschema` dep) |
| [`pyproject.toml`](pyproject.toml) | Publishable as the `mpf` pip package |

## Status

**v0.1.x** — schema is stable for the memory + KG-triples + memory-versions
+ compression-manifest record kinds. Forward-compatible: implementations
should skip unknown record kinds and unknown sidecar fields.

The reference implementation is [MNEMOS](https://github.com/perlowja/mnemos),
which produces and consumes MPF via its CHARON module and `/v1/export` /
`/v1/import` endpoints. MNEMOS is not the only producer or consumer —
anyone can target the spec.

## Quick validate

```bash
pip install jsonschema
python validate.py --file vectors/memory_basic.json
# → OK
```

## Adopting MPF in your memory system

If you maintain a memory system and want MPF support:

1. **Read [`MPF.md`](MPF.md)** — the field reference.
2. **Map your shape to `payload_version`** — declare your own (e.g.
   `mem0-1.x`), or target `mnemos-3.1` if your model fits.
3. **Round-trip the test vectors** — your import + export of `vectors/*.json`
   should preserve all fields. Unknown sidecars (kg_triples, memory_versions,
   compression_manifest) skip cleanly if you don't support them.
4. **Validate before shipping** — run `python validate.py --file <yours>`.

## Discussion

Spec-level / cross-system interop conversation lives at
[github.com/perlowja/mnemos/discussions](https://github.com/perlowja/mnemos/discussions)
under the **"the gods bring gifts"** master thread. File issues on this
repo for spec ambiguities, schema bugs, or vector-validation regressions.

## Roadmap

- **v0.1.x** — current: memories + KG triples + memory-versions DAG
  + compression manifest sidecars
- **v0.2** — federation contract surface (peer schema discovery, cursor
  formats); embedded attestations / provenance chain
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
