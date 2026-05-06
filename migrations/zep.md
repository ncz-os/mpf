# Zep to MPF v0.2

Best-effort offline adapter for Zep memory, graph, fact, and message exports. Public references used:

- https://help.getzep.com/v2/memory
- https://help.getzep.com/facts
- https://help.getzep.com/v2/understanding-the-graph
- https://help.getzep.com/searching-the-graph

## Source-data shape

The script accepts a JSON object with `facts`, `edges`, `results`, `graph.edges`, `messages`, `memory.messages`, or `chat_history`, or a bare JSON/JSONL array.

Fact/edge-like input:

```json
{
  "uuid": "edge-1",
  "fact": "Kendra likes Puma shoes.",
  "source_node_name": "Kendra",
  "name": "likes",
  "target_node_name": "Puma shoes",
  "created_at": "2026-01-15T10:30:00Z",
  "valid_at": "2026-01-15T00:00:00Z",
  "invalid_at": null,
  "graph_id": "user-graph"
}
```

Message-like input:

```json
{
  "id": "msg-1",
  "session_id": "session-1",
  "role": "human",
  "content": "I moved to Austin.",
  "created_at": "2026-01-15T10:30:00Z"
}
```

## MPF mapping

| Zep field | MPF v0.2 target |
|---|---|
| Fact `uuid`/`id` | `records[].id` with `zep_` prefix |
| `fact`, `content`, `summary` | `records[].payload.content` |
| Edge subject/name/object | `kg_triples[]` subject, predicate, object |
| `created_at` | `transaction_time`, `payload.created` |
| `valid_at` | `valid_time_start`, `kg_triples[].valid_from` |
| `invalid_at` | `valid_time_end`, `kg_triples[].valid_until` |
| `expired_at` | `payload.updated` fallback |
| `graph_id`, `group_id`, `user_id` | owner and namespace hints |
| Messages | `kind: "event"` with `event_type: "session_turn"` |
| Entire source object | `payload.metadata.zep_edge` or event metadata |

## Gotchas

- Zep stores facts on graph edges. The adapter emits both a memory record for the statement and a KG triple for the relationship.
- Zep distinguishes `created_at` and `expired_at` from valid-time fields. MPF maps this directly into transaction time and valid time.
- Zep context strings are derived output. Export raw messages and facts when possible.
- Group graphs and user graphs may use different identifiers; the adapter treats either as MPF namespace metadata.

## Runnable script

```bash
python3 migrations/zep.py zep-export.json -o zep.mpf.json
python3 validate.py --file zep.mpf.json
```

The script is file-based only. It does not call the Zep API.
