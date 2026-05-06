#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Any

from _adapter_common import compact_dict, envelope, first_value, list_from, load_json, memory_record, stable_id, write_json


def convert(data: Any, source_version: str) -> dict[str, Any]:
    records = []
    kg_triples = []
    chunks = []
    for key in ["documents", "chunks", "document_chunks", "summaries", "data_points", "results"]:
        chunks.extend(list_from(data, [key]))

    if isinstance(data, list):
        chunks = data

    for item in chunks:
        if not isinstance(item, dict):
            continue
        created = first_value(item, ["created_at", "created", "timestamp"])
        dataset = str(first_value(item, ["dataset_id", "dataset_name", "dataset"], "default"))
        records.append(
            memory_record(
                source_system="cognee",
                record_id=f"cognee_{first_value(item, ['id', 'uuid'], stable_id('chunk', item))}",
                content=first_value(item, ["text", "content", "summary", "page_content", "data"], item),
                category="cognee",
                subcategory=str(first_value(item, ["type", "kind", "data_type"], "chunk")),
                created=created,
                updated=first_value(item, ["updated_at", "modified_at"], created),
                owner_id=str(first_value(item, ["owner_id", "user_id"], "cognee-import")),
                namespace=dataset,
                metadata={"cognee": item},
                valid_start=first_value(item, ["valid_at", "created_at"], created),
                actor_type="system",
                actor_id="system:cognee",
                activity_id=f"cognee:dataset:{dataset}",
            )
        )

    for edge in list_from(data, ["edges", "graph.edges", "relationships", "triples"]):
        if not isinstance(edge, dict):
            continue
        kg_triples.append(
            compact_dict({
                "id": f"cognee_kg_{first_value(edge, ['id', 'uuid'], stable_id('edge', edge))}",
                "subject_literal": str(first_value(edge, ["source", "source_node", "subject", "from"], "unknown")),
                "predicate": str(first_value(edge, ["relationship", "relationship_name", "predicate", "type"], "relates_to")),
                "object_literal": str(first_value(edge, ["target", "target_node", "object", "to"], "unknown")),
                "confidence": first_value(edge, ["confidence", "score"], 1.0),
                "created": first_value(edge, ["created_at", "created"]),
                "metadata": {"cognee_edge": edge},
            })
        )

    return envelope(
        source_system="cognee",
        source_version=source_version,
        records=records,
        kg_triples=kg_triples,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a Cognee JSON export to MPF v0.2.")
    parser.add_argument("input", help="Cognee JSON export, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="unknown")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
