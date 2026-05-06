#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Any

from _adapter_common import compact_dict, envelope, event_record, first_value, list_from, load_json, memory_record, stable_id, write_json


def convert(data: Any, source_version: str) -> dict[str, Any]:
    records = []
    kg_triples = []
    edges = list_from(data, ["entity_edges", "edges", "facts", "results"])
    episodes = list_from(data, ["episodes", "episodic_nodes"])

    if isinstance(data, list):
        edges = [x for x in data if isinstance(x, dict) and ("fact" in x or "valid_at" in x)]
        episodes = [x for x in data if isinstance(x, dict) and ("episode_body" in x or "content" in x) and x not in edges]

    for edge in edges:
        if not isinstance(edge, dict):
            continue
        statement = first_value(edge, ["fact", "content", "name"], edge)
        created = first_value(edge, ["created_at", "created"])
        valid_at = first_value(edge, ["valid_at", "valid_from"], created)
        invalid_at = first_value(edge, ["invalid_at", "valid_until"])
        predicate = str(first_value(edge, ["name", "relationship", "predicate"], "relates_to"))
        rid = f"graphiti_{first_value(edge, ['uuid', 'id'], stable_id('edge', edge))}"
        records.append(
            memory_record(
                source_system="graphiti",
                record_id=rid,
                content=statement,
                category="graphiti_fact",
                subcategory=predicate,
                created=created,
                updated=first_value(edge, ["expired_at", "updated_at"], created),
                owner_id=str(first_value(edge, ["group_id", "graph_id"], "graphiti-import")),
                namespace=str(first_value(edge, ["group_id", "graph_id"], "default")),
                metadata={"graphiti_edge": edge, "episodes": edge.get("episodes")},
                valid_start=valid_at,
                valid_end=invalid_at,
                actor_type="system",
                actor_id="system:graphiti",
                activity_id=str(first_value(edge, ["episodes.0", "group_id"], "graphiti:edge-export")),
            )
        )
        kg_triples.append(
            compact_dict({
                "id": stable_id("graphiti_kg", edge),
                "subject_literal": str(first_value(edge, ["source_node_name", "source", "subject"], "unknown")),
                "predicate": predicate,
                "object_literal": str(first_value(edge, ["target_node_name", "target", "object"], statement)),
                "memory_id": rid,
                "valid_from": valid_at,
                "valid_until": invalid_at,
                "created": created,
                "metadata": {"graphiti_edge_id": first_value(edge, ["uuid", "id"])},
            })
        )

    for ep in episodes:
        if not isinstance(ep, dict):
            continue
        records.append(
            event_record(
                source_system="graphiti",
                record_id=f"graphiti_ep_{first_value(ep, ['uuid', 'id'], stable_id('episode', ep))}",
                event_type="ingest_event",
                content=first_value(ep, ["episode_body", "content", "body"], ep),
                occurred_at=first_value(ep, ["valid_at", "reference_time", "created_at"]),
                session_id=first_value(ep, ["group_id", "graph_id"]),
                actor=first_value(ep, ["source", "speaker"], "graphiti"),
                metadata={"graphiti_episode": ep},
            )
        )

    return envelope(
        source_system="graphiti",
        source_version=source_version,
        records=records,
        kg_triples=kg_triples,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Graphiti JSON export to MPF v0.2.")
    parser.add_argument("input", help="Graphiti JSON export, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
