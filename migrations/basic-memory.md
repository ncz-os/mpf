# Basic Memory to MPF v0.2

Best-effort offline adapter for Basic Memory Markdown or parsed JSON exports. Public references used:

- https://docs.basicmemory.com/guides/knowledge-format/
- https://docs.basicmemory.com/start-here/what-is-basic-memory
- https://docs.basicmemory.com/reference/technical-information

## Source-data shape

Basic Memory stores plain Markdown notes with YAML frontmatter, observations, and relations.

```markdown
---
title: API Authentication Decision
tags: [security, api]
permalink: api/authentication-decision
---

# API Authentication Decision

## Observations
- [decision] Use JWT tokens for API auth #security

## Relations
- depends_on [[User Service]]
```

The script accepts a Basic Memory directory, a single Markdown file, a parsed JSON object with `entities`, `notes`, `records`, or `items`, or stdin JSON.

## MPF mapping

| Basic Memory field | MPF v0.2 target |
|---|---|
| File path, `permalink`, title | Stable `records[].id` hash |
| Markdown body | `payload.content` |
| Frontmatter `type`, entity type | `payload.subcategory` |
| Frontmatter `tags` | `payload.metadata.tags` |
| Observations (`- [category] ...`) | `payload.metadata.observations` |
| Relations (`rel [[Target]]`) | `relations[]` when target is in export, else `kg_triples[]` |
| Frontmatter and parsed source | `payload.metadata.frontmatter` and `payload.metadata.source` |
| File sync operation | `provenance.wasGeneratedBy` |

## Gotchas

- The adapter includes a tiny frontmatter parser and does not require PyYAML. Complex nested YAML is preserved only as simple strings unless using a parsed JSON export.
- Basic Memory can parse observations anywhere in Markdown, not only under an `Observations` heading. The script follows the documented list-item pattern globally.
- Wiki-links that target notes outside the export become KG triples with literal objects.
- Markdown remains the content source of truth. MPF preserves the full body rather than trying to split every observation into a separate memory.

## Runnable script

```bash
python3 migrations/basic-memory.py /path/to/basic-memory-vault -o basic-memory.mpf.json
python3 validate.py --file basic-memory.mpf.json
```

The script is file-based only. It does not require a Basic Memory server.
