# Subcog to MPF v0.2

Best-effort offline adapter for Subcog git-note memory exports. Public references used:

- https://zircote.com/projects/subcog/
- https://zircote.com/blog/2026/01/new-productivity-plugins-skills/
- https://zircote.com/blog/2026/02/introducing-mif-memory-interchange-format/

## Source-data shape

Subcog is described publicly as a Claude Code memory system with git-native storage, semantic search, and namespaces. The adapter assumes an exported JSON object with `memories`, `notes`, `records`, or `items`, or a bare JSON/JSONL array.

```json
{
  "id": "note-1",
  "namespace": "patterns/python",
  "content": "Prefer pathlib for local filesystem paths.",
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-01-15T10:30:00Z",
  "git_note_ref": "refs/notes/subcog",
  "commit": "abc123",
  "tags": ["python", "style"]
}
```

## MPF mapping

| Subcog field | MPF v0.2 target |
|---|---|
| `id`, `uuid` | `records[].id` with `subcog_` prefix |
| `content`, `text`, `body`, `memory` | `payload.content` |
| `namespace` | `payload.namespace`, `payload.subcategory` |
| First namespace segment | `payload.category` |
| `created_at`, `timestamp` | transaction and valid-time defaults |
| `valid_at`, `valid_from`, `invalid_at`, `valid_until` | MPF bi-temporal fields |
| `git_note_ref`, `ref`, `commit`, `oid` | `provenance.wasInfluencedBy[]` as `git-note:<ref>` plus metadata |
| Entire source item | `payload.metadata.subcog` |

## Gotchas

- Public Subcog docs describe storage architecture more than a stable export schema. This adapter is intentionally conservative and preserves the raw item.
- Git notes are provenance, not MPF memory IDs. The script stores them as external influence URIs.
- If Subcog memories already follow MIF-style ontology namespaces, MPF keeps the namespace but does not align MPF's data model to MIF.
- Embeddings are not portable; re-embed after import.

## Runnable script

```bash
python3 migrations/subcog.py subcog-export.json -o subcog.mpf.json
python3 validate.py --file subcog.mpf.json
```

The script is file-based only. It does not inspect a git repository or call an MCP server.
