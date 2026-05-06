#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Any

from _adapter_common import (
    compact_dict,
    envelope,
    event_record,
    first_value,
    list_from,
    load_json,
    memory_record,
    stable_id,
    write_json,
)


def convert(data: Any, source_version: str) -> dict[str, Any]:
    records = []
    kg_triples = []
    facts = list_from(data, ["facts", "edges", "results", "graph.edges"])
    messages = list_from(data, ["messages", "memory.messages", "chat_history"])

    if isinstance(data, list):
        messages = [x for x in data if isinstance(x, dict) and "role" in x and "content" in x]
        facts = [x for x in data if isinstance(x, dict) and x not in messages]

    for edge in facts:
        if not isinstance(edge, dict):
            continue
        statement = first_value(edge, ["fact", "content", "summary", "name"], edge)
        created = first_value(edge, ["created_at", "created"])
        valid_at = first_value(edge, ["valid_at", "valid_from"], created)
        invalid_at = first_value(edge, ["invalid_at", "valid_until"])
        source = first_value(edge, ["source", "source_node", "source_node_name", "subject"], "")
        target = first_value(edge, ["target", "target_node", "target_node_name", "object"], "")
        predicate = first_value(edge, ["relationship", "relationship_type", "name", "predicate"], "relates_to")
        rid = f"zep_{first_value(edge, ['uuid', 'id'], stable_id('edge', edge))}"
        records.append(
            memory_record(
                source_system="zep",
                record_id=rid,
                content=statement,
                category="zep_fact",
                subcategory=str(predicate),
                created=created,
                updated=first_value(edge, ["expired_at", "updated_at"], created),
                owner_id=str(first_value(edge, ["user_id", "graph_id"], "zep-import")),
                namespace=str(first_value(edge, ["group_id", "graph_id", "session_id"], "default")),
                metadata={"zep_edge": edge},
                valid_start=valid_at,
                valid_end=invalid_at,
                actor_type="system",
                actor_id="system:zep",
                activity_id=str(first_value(edge, ["episode_id", "graph_id"], "zep:graph-export")),
            )
        )
        kg_triples.append(
            compact_dict({
                "id": stable_id("zep_kg", edge),
                "subject_literal": str(source or "unknown"),
                "predicate": str(predicate),
                "object_literal": str(target or statement),
                "memory_id": rid,
                "valid_from": valid_at,
                "valid_until": invalid_at,
                "created": created,
                "metadata": {"zep_edge_id": first_value(edge, ["uuid", "id"])},
            })
        )

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        records.append(
            event_record(
                source_system="zep",
                record_id=f"zep_evt_{first_value(msg, ['uuid', 'id'], stable_id('msg', msg))}",
                event_type="session_turn",
                content=first_value(msg, ["content", "text"], msg),
                occurred_at=first_value(msg, ["created_at", "timestamp", "role_time"]),
                session_id=first_value(msg, ["session_id", "thread_id"]),
                actor=first_value(msg, ["role", "role_type", "actor"]),
                metadata={"zep_message": msg},
            )
        )

    return envelope(
        source_system="zep",
        source_version=source_version,
        records=records,
        kg_triples=kg_triples,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Zep graph or memory JSON export to MPF v0.2.")
    parser.add_argument("input", help="Zep JSON export, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
