#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def convert(data: Any, source_version: str) -> dict[str, Any]:
    items = list_from(data, ["results", "memories", "records", "items", "data"])
    records = []
    for item in items:
        if not isinstance(item, dict):
            continue
        content = first_value(item, ["memory", "text", "data.memory", "content"], item)
        created = first_value(item, ["created_at", "created", "timestamp"])
        updated = first_value(item, ["updated_at", "updated"], created)
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        user_id = first_value(item, ["user_id", "owner"])
        agent_id = item.get("agent_id")
        actor_type = "user" if user_id else "agent" if agent_id else "system"
        actor_id = f"user:{user_id}" if user_id else f"agent:{agent_id}" if agent_id else "system:mem0"
        influences = []
        source_url = metadata.get("source_url") or metadata.get("url")
        if source_url:
            influences.append({"type": "external_uri", "uri": source_url, "relationship": "source"})
        category = metadata.get("category") or "mem0"
        raw_id = first_value(item, ["id", "memory_id", "hash"], content)
        records.append(
            memory_record(
                source_system="mem0",
                record_id=f"mem0_{raw_id}" if isinstance(raw_id, str) else stable_id("mem0", item),
                content=content,
                category=str(category),
                subcategory="memory",
                created=created,
                updated=updated,
                owner_id=str(user_id or "mem0-import"),
                namespace=str(first_value(item, ["run_id", "app_id", "project_id"], "default")),
                metadata={
                    "mem0": {k: v for k, v in item.items() if k != "metadata"},
                    "source_metadata": metadata,
                },
                valid_start=first_value(item, ["valid_at", "timestamp", "created_at"], created),
                valid_end=first_value(item, ["expiration_date", "expires_at"]),
                actor_type=actor_type,
                actor_id=actor_id,
                activity_id=str(first_value(item, ["run_id", "app_id"], "mem0:export")),
                influences=influences,
            )
        )
    return envelope(source_system="mem0", source_version=source_version, records=records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Mem0 JSON export to MPF v0.2.")
    parser.add_argument("input", help="Mem0 JSON export, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
