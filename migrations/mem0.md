# Mem0 to MPF v0.2

Best-effort offline adapter for Mem0 memory exports. Public references used:

- https://docs.mem0.ai/api-reference/memory/get-memories
- https://docs.mem0.ai/api-reference/memory/add-memories
- https://docs.mem0.ai/platform/features/v2-memory-filters

## Source-data shape

The script expects a JSON object with `results`, `memories`, `records`, `items`, or `data`, or a bare JSON/JSONL array. Each item may include:

```json
{
  "id": "mem_123",
  "memory": "The user prefers Python for automation.",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z",
  "user_id": "alice",
  "agent_id": "agent-1",
  "run_id": "run-1",
  "metadata": {"category": "preference", "source_url": "https://example.com"}
}
```

The adapter also accepts older/update shapes where content is under `text`, `content`, or `data.memory`.

## MPF mapping

| Mem0 field | MPF v0.2 target |
|---|---|
| `id`, `memory_id`, `hash` | `records[].id` with `mem0_` prefix |
| `memory`, `text`, `data.memory`, `content` | `records[].payload.content` |
| `metadata.category` | `records[].payload.category` |
| `user_id` | `payload.owner_id` and `provenance.wasAttributedTo` as `type: "user"` |
| `agent_id` | `provenance.wasAttributedTo` as `type: "agent"` when no `user_id` exists |
| `run_id`, `app_id`, `project_id` | `payload.namespace` and activity hints |
| `created_at`, `timestamp` | `transaction_time`, `payload.created`, default `valid_time_start` |
| `expiration_date`, `expires_at` | `valid_time_end` |
| `metadata.source_url` | `provenance.wasInfluencedBy[]` external URI |
| Entire source item | `payload.metadata.mem0` |

## Gotchas

- Mem0 may return asynchronous add events rather than finalized memories. The adapter maps `data.memory` from those events but preserves the event object in metadata.
- Mem0 graph output can include entities/relationships. This script keeps that raw data in metadata instead of trying to infer MPF `kg_triples`.
- Date-only `expiration_date` values are normalized to UTC midnight.
- If Mem0 returns both `user_id` and `agent_id`, MPF attributes the memory to the user and keeps agent identifiers in metadata.

## Runnable script

```bash
python3 migrations/mem0.py mem0-export.json -o mem0.mpf.json
python3 validate.py --file mem0.mpf.json
```

The script is file-based only. It does not call the Mem0 API.
