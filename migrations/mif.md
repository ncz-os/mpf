# MIF to MPF v0.2

Read-only, one-way adapter from MIF JSON-LD into MPF v0.2. MPF uses MIF as a reference for ideas only. MNEMOS does not align its data model to MIF and this adapter does not merge or write back to MIF.

Public references used:

- https://mif-spec.dev/
- https://mif-spec.dev/specification/json-ld-format/
- https://mif-spec.dev/specification/data-model/
- https://mif-spec.dev/guides/schema-reference/
- https://zircote.com/blog/2026/02/introducing-mif-memory-interchange-format/

## Source-data shape

The script accepts a single MIF `.memory.json`, a JSON-LD object with `@graph`, a JSON object with `memories`, or a JSON/JSONL array.

```json
{
  "@context": "https://mif-spec.dev/schema/context.jsonld",
  "@type": "Memory",
  "@id": "urn:mif:550e8400-e29b-41d4-a716-446655440000",
  "memoryType": "semantic",
  "namespace": "_semantic/preferences",
  "content": "User prefers dark mode for all applications.",
  "created": "2026-01-15T10:30:00Z",
  "temporal": {
    "validFrom": "2026-01-15T00:00:00Z",
    "validUntil": null,
    "recordedAt": "2026-01-15T10:30:00Z"
  },
  "provenance": {
    "confidence": 0.95,
    "prov:wasDerivedFrom": {"@id": "urn:mif:conversation:conv-456"}
  }
}
```

## MPF mapping

| MIF field | MPF v0.2 target |
|---|---|
| `@id`, `mif:id`, `id` | `records[].id` with `mif_` prefix |
| `content`, `mif:content` | `payload.content` |
| `memoryType`, `mif:memoryType`, `type` | `payload.category` |
| `namespace`, `mif:namespace` | `payload.namespace`, `payload.subcategory` |
| `created`, `dc:created`, `temporal.recordedAt` | `transaction_time`, payload timestamps |
| `temporal.validFrom` | `valid_time_start` |
| `temporal.validUntil` | `valid_time_end` |
| `provenance.prov:wasDerivedFrom` | `provenance.wasInfluencedBy[]` external URI |
| MIF relationships to included memories | MPF `relations[]` |
| Entire MIF object | `payload.metadata.mif_raw` |

## Gotchas

- This is a one-way adapter. It preserves `mif_raw` for audit and possible reconstruction, but it does not claim MPF and MIF are equivalent.
- MIF uses JSON-LD and PROV-O names. MPF v0.2 uses compact PROV-DM-inspired JSON fields with explicit type discriminators.
- MIF Markdown frontmatter is not parsed by this script. Convert Markdown to MIF JSON-LD first or use a JSON export.
- MIF relationship and ontology semantics are preserved as metadata unless the target memory is present in the same input bundle.
- No upstream contribution or MIF merge workflow is implied.

## Runnable script

```bash
python3 migrations/mif.py memory.memory.json -o mif-readonly.mpf.json
python3 validate.py --file mif-readonly.mpf.json
```

The script is file-based only and intentionally read-only.
