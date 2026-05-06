#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Any

from _adapter_common import (
    envelope,
    event_record,
    first_value,
    list_from,
    load_json,
    memory_record,
    stable_id,
    write_json,
)


def _collect_lists(data: Any, keys: list[str]) -> list[Any]:
    out: list[Any] = []
    if isinstance(data, dict):
        for key in keys:
            out.extend(list_from(data, [key]))
    elif isinstance(data, list):
        out.extend(data)
    return out


def convert(data: Any, source_version: str) -> dict[str, Any]:
    records = []
    agent_id = first_value(data, ["id", "agent_id"], "letta-agent") if isinstance(data, dict) else "letta-agent"

    blocks = _collect_lists(data, ["memory_blocks", "blocks", "core_memory.blocks", "memory.blocks"])
    for block in blocks:
        if not isinstance(block, dict):
            continue
        label = first_value(block, ["label", "id", "name"], "block")
        created = first_value(block, ["created_at", "created"])
        records.append(
            memory_record(
                source_system="letta",
                record_id=f"letta_block_{first_value(block, ['id'], stable_id('block', block))}",
                content=first_value(block, ["value", "content", "text"], block),
                category="letta_core_memory",
                subcategory=str(label),
                created=created,
                updated=first_value(block, ["updated_at", "modified_at"], created),
                owner_id=str(agent_id),
                namespace=str(label),
                metadata={"letta_block": block},
                valid_start=created,
                actor_type="agent",
                actor_id=f"agent:{agent_id}",
                activity_id=f"letta:block:{label}",
            )
        )

    archival = _collect_lists(data, ["archival_memory", "archival_memories", "passages", "sources"])
    for item in archival:
        if not isinstance(item, dict):
            continue
        created = first_value(item, ["created_at", "created"])
        records.append(
            memory_record(
                source_system="letta",
                record_id=f"letta_archival_{first_value(item, ['id'], stable_id('archival', item))}",
                content=first_value(item, ["text", "content", "value"], item),
                category="letta_archival_memory",
                subcategory=str(first_value(item, ["label", "source", "type"], "archival")),
                created=created,
                updated=first_value(item, ["updated_at", "modified_at"], created),
                owner_id=str(agent_id),
                namespace="archival",
                metadata={"letta_archival": item},
                valid_start=created,
                actor_type="agent",
                actor_id=f"agent:{agent_id}",
                activity_id="letta:archival-memory",
            )
        )

    messages = _collect_lists(data, ["messages", "conversation", "in_context_messages"])
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        records.append(
            event_record(
                source_system="letta",
                record_id=f"letta_evt_{first_value(msg, ['id'], stable_id('msg', msg))}",
                event_type="session_turn",
                content=first_value(msg, ["content", "text"], msg),
                occurred_at=first_value(msg, ["created_at", "timestamp"]),
                session_id=str(agent_id),
                actor=first_value(msg, ["role", "message_type", "actor"]),
                metadata={"letta_message": msg},
            )
        )

    return envelope(source_system="letta", source_version=source_version, records=records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Letta agent export to MPF v0.2.")
    parser.add_argument("input", help="Letta JSON export, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
