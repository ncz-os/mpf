# MPF test vectors

Canonical fixtures every conformant MPF implementation should accept,
parse without error, and (for round-trip implementations) re-emit
without loss of any fields it claims to support.

## Files

| File | Covers |
|---|---|
| `memory_basic.json` | Two `kind: "memory"` records, no sidecars. The minimum-shape envelope. |
| `memory_with_kg.json` | One memory + 2 KG triples in the `kg_triples` sidecar. Tests subject_literal/object_literal + memory_id linkage. |
| `memory_with_versions.json` | One memory + 2 memory-version DAG entries (parent → child). Tests `memory_versions` sidecar with `parent_version_id`. |
| `provenance_full_chain.json` | MPF v0.2 PROV chain with `wasInfluencedBy` pointing at another memory in the same envelope plus compression lineage. |
| `memory_bitemporal.json` | MPF v0.2 memory where valid time differs from transaction time. |
| `migration_from_mif_round_trip.json` | MPF v0.2 output from the read-only MIF adapter, preserving the source MIF object for one-way reconstruction. |

## Validation

```bash
pip install jsonschema
python ../validate.py --file memory_basic.json
python ../validate.py --file memory_with_kg.json
python ../validate.py --file memory_with_versions.json
python ../validate.py .
```

All vectors should print a summary line ending in `OK`.

## Round-trip contract

For an implementation that supports a given record kind / sidecar:

1. **Import** the vector
2. **Export** it back out via the implementation's MPF emitter
3. **Compare** — the resulting envelope MUST be field-equivalent to the
   original for every field that maps to the implementation's native
   schema. Fields the implementation doesn't model may be dropped, but
   that constitutes a documented lossy mapping (see [`MPF.md`](../MPF.md)
   "Interop mapping per peer system").

For implementations that do NOT support a given sidecar:

1. **Import** the vector — should succeed by skipping the unsupported
   sidecar.
2. The records the implementation DOES support must come through cleanly.
3. Re-emitted envelopes will lack the unsupported sidecar — that's expected.

## Adding new vectors

When new record kinds, sidecar shapes, or edge cases are added to the
spec, add a new vector here and update this README. PRs welcome.
