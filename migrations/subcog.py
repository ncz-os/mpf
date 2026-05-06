#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Any

from _adapter_common import envelope, first_value, list_from, load_json, memory_record, stable_id, write_json


def convert(data: Any, source_version: str) -> dict[str, Any]:
    items = list_from(data, ["memories", "notes", "records", "items"])
    records = []
    for item in items:
        if not isinstance(item, dict):
            continue
        namespace = str(first_value(item, ["namespace", "category", "scope"], "subcog"))
        category = namespace.split("/")[0] if namespace else "subcog"
        created = first_value(item, ["created_at", "created", "timestamp"])
        source_ref = first_value(item, ["git_note_ref", "ref", "commit", "oid"])
        influences = []
        if source_ref:
            influences.append({"type": "external_uri", "uri": f"git-note:{source_ref}", "relationship": "source"})
        records.append(
            memory_record(
                source_system="subcog",
                record_id=f"subcog_{first_value(item, ['id', 'uuid'], stable_id('note', item))}",
                content=first_value(item, ["content", "text", "body", "memory"], item),
                category=category,
                subcategory=namespace,
                created=created,
                updated=first_value(item, ["updated_at", "modified", "timestamp"], created),
                owner_id=str(first_value(item, ["owner", "user", "repo"], "subcog-import")),
                namespace=namespace,
                metadata={"subcog": item},
                valid_start=first_value(item, ["valid_at", "valid_from"], created),
                valid_end=first_value(item, ["invalid_at", "valid_until"]),
                actor_type="agent",
                actor_id=str(first_value(item, ["agent", "model"], "agent:subcog")),
                activity_id=str(source_ref or "subcog:git-notes-export"),
                influences=influences,
            )
        )
    return envelope(source_system="subcog", source_version=source_version, records=records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Subcog JSON export to MPF v0.2.")
    parser.add_argument("input", help="Subcog JSON export, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
