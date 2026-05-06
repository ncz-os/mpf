# MemPalace to MPF v0.2

Best-effort offline adapter for MemPalace JSON exports. Public references used:

- https://mempalace.github.io/mempalace/concepts/agents.html
- https://www.mempalace.net/download
- https://www.mempalace.net/

## Source-data shape

Public MemPalace docs describe wings, rooms, agent diaries, compressed entries, and temporal knowledge-graph triples. The adapter accepts nested JSON with keys such as `wings`, `rooms`, `halls`, `drawers`, `cards`, `memories`, `diary_entries`, `entries`, `kg_triples`, or `triples`.

```json
{
  "wings": [
    {
      "name": "python",
      "rooms": [
        {
          "name": "style",
          "cards": [
            {"id": "card-1", "content": "Use pathlib for filesystem paths.", "created_at": "2026-01-15T10:30:00Z"}
          ]
        }
      ]
    }
  ],
  "kg_triples": [
    {"subject": "pathlib", "predicate": "preferred_for", "object": "filesystem paths"}
  ]
}
```

## MPF mapping

| MemPalace field | MPF v0.2 target |
|---|---|
| Card/entry `id` | `records[].id` with `mempalace_` prefix |
| `content`, `entry`, `text`, `memory`, `summary` | `payload.content` |
| Wing/category | `payload.category` |
| Room/drawer/agent | `payload.subcategory` |
| Nested palace path | `payload.namespace` and `payload.metadata.mempalace_path` |
| Diary `agent_name` | owner/provenance actor hint |
| `valid_at`, `valid_from`, `invalid_at`, `valid_until` | MPF bi-temporal fields |
| `kg_triples`, `triples`, `graph.edges` | MPF `kg_triples[]` |
| Entire card | `payload.metadata.mempalace_card` |

## Gotchas

- Public MemPalace docs emphasize user-facing concepts and MCP workflows, not a stable export schema. The script recursively walks common container names and preserves raw cards.
- Spatial layout is preserved only if it appears in the source card object.
- AAAK or other compressed forms are kept in raw metadata unless a source export already separates compression contest data.
- Temporal KG triples map cleanly when source triples include validity fields.

## Runnable script

```bash
python3 migrations/mempalace.py mempalace-export.json -o mempalace.mpf.json
python3 validate.py --file mempalace.mpf.json
```

The script is file-based only. It does not call MemPalace MCP tools.
