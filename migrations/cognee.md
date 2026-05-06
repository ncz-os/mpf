# Cognee to MPF v0.2

Best-effort offline adapter for Cognee dataset, chunk, summary, and graph exports. Public references used:

- https://docs.cognee.ai/core-concepts/overview
- https://docs.cognee.ai/core-concepts/main-operations/cognify
- https://docs.cognee.ai/core-concepts/main-operations/search

## Source-data shape

Cognee ingests data, cognifies it into chunks, summaries, embeddings, graph nodes/edges, and dataset-scoped stores. The adapter accepts JSON with `documents`, `chunks`, `document_chunks`, `summaries`, `data_points`, `results`, `edges`, `relationships`, or `triples`.

```json
{
  "dataset_id": "dataset-1",
  "chunks": [
    {
      "id": "chunk-1",
      "text": "MNEMOS uses MPF for memory portability.",
      "dataset_id": "dataset-1",
      "created_at": "2026-01-15T10:30:00Z"
    }
  ],
  "edges": [
    {"source": "MNEMOS", "relationship": "uses", "target": "MPF"}
  ]
}
```

## MPF mapping

| Cognee field | MPF v0.2 target |
|---|---|
| Chunk/document `id`, `uuid` | `records[].id` with `cognee_` prefix |
| `text`, `content`, `summary`, `page_content`, `data` | `payload.content` |
| `type`, `kind`, `data_type` | `payload.subcategory` |
| `dataset_id`, `dataset_name` | `payload.namespace` and activity id |
| `created_at`, `timestamp` | transaction and default valid time |
| `owner_id`, `user_id` | `payload.owner_id` |
| Graph `edges`, `relationships`, `triples` | `kg_triples[]` |
| Entire source object | `payload.metadata.cognee` |

## Gotchas

- Cognee embeddings and vector indexes are implementation-specific. The adapter does not export vectors.
- Cognee graph nodes and summaries may be generated artifacts. MPF preserves their source object so importers can choose whether to treat them as memories or regenerate them.
- Dataset permissions are represented only as metadata unless explicit owner fields are present.
- If the source graph uses internal node IDs without names, MPF stores those IDs as literals.

## Runnable script

```bash
python3 migrations/cognee.py cognee-export.json -o cognee.mpf.json
python3 validate.py --file cognee.mpf.json
```

The script is file-based only. It does not call Cognee server endpoints.
