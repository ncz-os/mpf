#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Any

from _adapter_common import compact_dict, envelope, first_value, list_from, load_json, memory_record, stable_id, write_json


def walk_cards(node: Any, path: list[str] | None = None) -> list[tuple[dict[str, Any], list[str]]]:
    path = path or []
    out: list[tuple[dict[str, Any], list[str]]] = []
    if isinstance(node, list):
        for child in node:
            out.extend(walk_cards(child, path))
        return out
    if not isinstance(node, dict):
        return out

    content = first_value(node, ["content", "entry", "text", "memory", "card", "summary"])
    if content:
        out.append((node, path))

    for key in ["wings", "rooms", "halls", "drawers", "cards", "memories", "diary_entries", "entries"]:
        for child in node.get(key, []) if isinstance(node.get(key), list) else []:
            label = str(first_value(child, ["name", "title", "id", "agent_name"], key))
            out.extend(walk_cards(child, path + [label]))
    return out


def convert(data: Any, source_version: str) -> dict[str, Any]:
    records = []
    kg_triples = []
    for card, path in walk_cards(data):
        created = first_value(card, ["created_at", "created", "timestamp"])
        category = str(first_value(card, ["wing", "category", "type"], path[0] if path else "mempalace"))
        subcategory = str(first_value(card, ["room", "drawer", "agent_name"], path[-1] if path else "memory"))
        records.append(
            memory_record(
                source_system="mempalace",
                record_id=f"mempalace_{first_value(card, ['id', 'uuid'], stable_id('card', card, path))}",
                content=first_value(card, ["content", "entry", "text", "memory", "card", "summary"], card),
                category=category,
                subcategory=subcategory,
                created=created,
                updated=first_value(card, ["updated_at", "modified_at"], created),
                owner_id=str(first_value(card, ["agent_name", "owner", "user"], "mempalace-import")),
                namespace="/".join(path) or category,
                metadata={"mempalace_path": path, "mempalace_card": card},
                valid_start=first_value(card, ["valid_at", "valid_from"], created),
                valid_end=first_value(card, ["invalid_at", "valid_until"]),
                actor_type="agent",
                actor_id=f"agent:{first_value(card, ['agent_name'], 'mempalace')}",
                activity_id="mempalace:export",
            )
        )

    for triple in list_from(data, ["kg_triples", "triples", "graph.edges"]):
        if not isinstance(triple, dict):
            continue
        kg_triples.append(
            compact_dict({
                "id": f"mempalace_kg_{first_value(triple, ['id'], stable_id('kg', triple))}",
                "subject_literal": str(first_value(triple, ["subject", "source", "from"], "unknown")),
                "predicate": str(first_value(triple, ["predicate", "relation", "type"], "relates_to")),
                "object_literal": str(first_value(triple, ["object", "target", "to"], "unknown")),
                "valid_from": first_value(triple, ["valid_at", "valid_from", "created_at"]),
                "valid_until": first_value(triple, ["invalid_at", "valid_until"]),
                "created": first_value(triple, ["created_at", "created"]),
                "metadata": {"mempalace_triple": triple},
            })
        )

    return envelope(
        source_system="mempalace",
        source_version=source_version,
        records=records,
        kg_triples=kg_triples,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a MemPalace JSON export to MPF v0.2.")
    parser.add_argument("input", help="MemPalace JSON export, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
