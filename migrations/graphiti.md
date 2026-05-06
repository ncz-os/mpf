# Graphiti to MPF v0.2

Best-effort offline adapter for Graphiti temporal graph exports. Public references used:

- https://help.getzep.com/graphiti/core-concepts/adding-episodes
- https://help.getzep.com/facts
- https://help.getzep.com/understanding-the-graph

## Source-data shape

Graphiti models episodes plus entity edges that carry facts and temporal attributes.

```json
{
  "entity_edges": [
    {
      "uuid": "edge-1",
      "fact": "Kendra likes Puma shoes.",
      "name": "likes",
      "source_node_name": "Kendra",
      "target_node_name": "Puma shoes",
      "episodes": ["episode-1"],
      "created_at": "2026-01-15T10:30:00Z",
      "valid_at": "2026-01-15T00:00:00Z",
      "invalid_at": null
    }
  ],
  "episodes": [
    {"uuid": "episode-1", "episode_body": "Kendra: I like Puma shoes.", "reference_time": "2026-01-15T00:00:00Z"}
  ]
}
```

## MPF mapping

| Graphiti field | MPF v0.2 target |
|---|---|
| Edge `uuid`, `id` | `records[].id` with `graphiti_` prefix |
| Edge `fact` | `payload.content` |
| Edge `name` | `payload.subcategory`, `kg_triples[].predicate` |
| Edge source/target names | `kg_triples[]` literals |
| `valid_at` | `valid_time_start`, `kg_triples[].valid_from` |
| `invalid_at` | `valid_time_end`, `kg_triples[].valid_until` |
| `created_at` | transaction time |
| `episodes` | `payload.metadata.episodes` |
| Episode body/content | `kind: "event"`, `event_type: "ingest_event"` |

## Gotchas

- Graphiti's `created_at` is transaction time, while `valid_at` and `invalid_at` describe real-world validity. MPF v0.2 preserves that distinction.
- Bulk ingestion may skip invalidation behavior. If the source export lacks invalidation timestamps, MPF leaves valid end open-ended.
- Graphiti episode nodes are provenance for extracted facts. The adapter emits them as MPF event records and stores episode IDs on edge-derived memories.
- Entity node summaries are not converted unless included as edge or episode data.

## Runnable script

```bash
python3 migrations/graphiti.py graphiti-export.json -o graphiti.mpf.json
python3 validate.py --file graphiti.mpf.json
```

The script is file-based only. It does not connect to Neo4j or a Graphiti service.
