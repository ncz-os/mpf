#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from _adapter_common import (
    envelope,
    first_value,
    list_from,
    load_json,
    memory_record,
    stable_id,
    write_json,
)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    body = text[text.find("\n", end + 1) + 1 :]
    meta: dict[str, Any] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [x.strip().strip("'\"") for x in value[1:-1].split(",") if x.strip()]
        else:
            meta[key.strip()] = value.strip("'\"")
    return meta, body


def parse_markdown_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    title = frontmatter.get("title") or (heading.group(1).strip() if heading else path.stem)
    observations = [
        {"category": m.group(1), "content": m.group(2).strip()}
        for m in re.finditer(r"^\s*-\s+\[([^\]]+)\]\s+(.+)$", body, re.MULTILINE)
        if m.group(1).strip() not in {" ", "x", "X"}
    ]
    relations = [
        {"rel": m.group(1), "target": m.group(2)}
        for m in re.finditer(r"^\s*-\s+([A-Za-z0-9_-]+)\s+\[\[([^\]]+)\]\]", body, re.MULTILINE)
    ]
    return {
        "title": title,
        "frontmatter": frontmatter,
        "body": body.strip(),
        "observations": observations,
        "relations": relations,
        "file_path": str(path),
    }


def load_source(path: str) -> list[dict[str, Any]]:
    source = Path(path)
    if source.is_dir():
        return [parse_markdown_file(p) for p in sorted(source.rglob("*.md"))]
    if source.suffix.lower() == ".md":
        return [parse_markdown_file(source)]
    data = load_json(path)
    return list_from(data, ["entities", "notes", "records", "items"])


def convert(items: list[dict[str, Any]], source_version: str) -> dict[str, Any]:
    records = []
    relations = []
    kg_triples = []
    title_to_id: dict[str, str] = {}

    for item in items:
        title = str(first_value(item, ["title", "name", "permalink"], stable_id("basic_memory", item)))
        rid = stable_id("basic_memory", first_value(item, ["permalink", "file_path", "id"], title))
        title_to_id[title] = rid
        frontmatter = item.get("frontmatter") or item.get("entity_metadata") or {}
        tags = frontmatter.get("tags") if isinstance(frontmatter, dict) else None
        category = str(first_value(item, ["type", "entity_type"], "note"))
        records.append(
            memory_record(
                source_system="basic-memory",
                record_id=rid,
                content=first_value(item, ["body", "content", "text"], title),
                category="basic_memory",
                subcategory=category,
                created=first_value(item, ["created_at", "created"]),
                updated=first_value(item, ["updated_at", "modified"]),
                owner_id="basic-memory-import",
                namespace=str(first_value(item, ["permalink", "file_path"], title)),
                metadata={
                    "title": title,
                    "tags": tags,
                    "frontmatter": frontmatter,
                    "observations": item.get("observations", []),
                    "relations": item.get("relations", []),
                    "source": item,
                },
                activity_id="basic-memory:markdown-sync",
            )
        )

    for item in items:
        title = str(first_value(item, ["title", "name", "permalink"], ""))
        from_id = title_to_id.get(title)
        if not from_id:
            continue
        for rel in item.get("relations", []):
            target = str(rel.get("target") or rel.get("to_name") or rel.get("to_id") or "")
            rel_name = str(rel.get("rel") or rel.get("relation_type") or "relates_to")
            to_id = title_to_id.get(target)
            if to_id:
                relations.append({"from": from_id, "rel": rel_name, "to": to_id})
            else:
                kg_triples.append(
                    {
                        "id": stable_id("basic_memory_kg", from_id, rel),
                        "subject_id": from_id,
                        "predicate": rel_name,
                        "object_literal": target,
                        "memory_id": from_id,
                    }
                )

    return envelope(
        source_system="basic-memory",
        source_version=source_version,
        records=records,
        kg_triples=kg_triples,
        relations=relations,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Basic Memory Markdown or JSON to MPF v0.2.")
    parser.add_argument("input", help="Basic Memory directory, Markdown file, JSON export, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_source(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
