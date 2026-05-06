# Letta to MPF v0.2

Best-effort offline adapter for Letta agent exports. Public references used:

- https://docs.letta.com/guides/agents/memory-blocks/
- https://docs.letta.com/guides/core-concepts/memory/archival-memory/
- https://docs.letta.com/api/resources/agents/subresources/blocks/

## Source-data shape

The script accepts an agent export object with `memory_blocks`, `blocks`, `core_memory.blocks`, `memory.blocks`, `archival_memory`, `archival_memories`, `passages`, `sources`, or `messages`.

```json
{
  "id": "agent-000",
  "memory_blocks": [
    {
      "id": "block-1",
      "label": "human",
      "value": "The human prefers Python.",
      "limit": 5000,
      "description": "Facts about the human",
      "created_at": "2026-01-15T10:30:00Z"
    }
  ],
  "archival_memory": [
    {"id": "arch-1", "text": "Project uses Postgres.", "created_at": "2026-01-15T11:00:00Z"}
  ],
  "messages": [
    {"id": "msg-1", "role": "user", "content": "Remember this.", "created_at": "2026-01-15T11:05:00Z"}
  ]
}
```

## MPF mapping

| Letta field | MPF v0.2 target |
|---|---|
| Agent `id` | `payload.owner_id`, event `session_id`, provenance actor |
| Block `id` | `records[].id` with `letta_block_` prefix |
| Block `label` | `payload.subcategory` and namespace |
| Block `value` | `payload.content` |
| Block `description`, `limit`, other fields | `payload.metadata.letta_block` |
| Archival text/content | `kind: "memory"`, category `letta_archival_memory` |
| Messages | `kind: "event"`, `event_type: "session_turn"` |
| `created_at`, `updated_at` | transaction and payload timestamps |

## Gotchas

- Letta core memory blocks are always-visible context, not retrieved memories. MPF records preserve the block label so importers can decide whether to recreate blocks or store ordinary memories.
- Updating a Letta block replaces the full block value. MPF does not infer intra-block edit history unless a source export includes it.
- Archival memory is semantically searchable and maps more naturally to regular MPF memory records.
- Shared blocks may be attached to multiple agents. This adapter preserves the source block metadata but does not duplicate cross-agent attachment graphs.

## Runnable script

```bash
python3 migrations/letta.py letta-agent-export.json -o letta.mpf.json
python3 validate.py --file letta.mpf.json
```

The script is file-based only. It does not call the Letta API.
