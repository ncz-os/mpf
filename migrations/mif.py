#!/usr/bin/env python3
from __future__ import annotations

import argparse
from typing import Any

from _adapter_common import envelope, first_value, list_from, load_json, memory_record, stable_id, write_json


def _mif_items(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if isinstance(data.get("@graph"), list):
            return [x for x in data["@graph"] if isinstance(x, dict)]
        if isinstance(data.get("memories"), list):
            return [x for x in data["memories"] if isinstance(x, dict)]
        return [data]
    return []


def _compact_mif_id(value: Any) -> str:
    text = str(value or "")
    for prefix in ["urn:mif:memory:", "urn:mif:"]:
        if text.startswith(prefix):
            return text[len(prefix) :]
    return text or stable_id("mif", value)


def convert(data: Any, source_version: str) -> dict[str, Any]:
    records = []
    items = _mif_items(data)
    mif_to_mpf: dict[str, str] = {}
    for item in items:
        mif_id = first_value(item, ["@id", "mif:id", "id"], stable_id("mif", item))
        mpf_id = f"mif_{_compact_mif_id(mif_id)}"
        mif_to_mpf[str(mif_id)] = mpf_id

    relations = []
    for item in items:
        mif_id = first_value(item, ["@id", "mif:id", "id"], stable_id("mif", item))
        mpf_id = mif_to_mpf[str(mif_id)]
        temporal = item.get("temporal") if isinstance(item.get("temporal"), dict) else {}
        prov = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
        generated = (
            first_value(temporal, ["recordedAt"])
            or first_value(item, ["created", "dc:created", "mif:created"])
        )
        associated = first_value(
            prov,
            [
                "prov:wasGeneratedBy.prov:wasAssociatedWith.@id",
                "wasGeneratedBy.wasAssociatedWith.id",
                "agent",
            ],
            "agent:mif",
        )
        influences = []
        derived = first_value(prov, ["prov:wasDerivedFrom.@id", "wasDerivedFrom.id", "source"])
        if derived:
            influences.append({"type": "external_uri", "uri": str(derived), "relationship": "mif:derived_from"})
        for rel in list_from(item, ["relationships", "mif:relationships"]):
            target = first_value(rel, ["target.@id", "mif:target", "target"])
            if target and str(target) in mif_to_mpf:
                relations.append(
                    {
                        "from": mpf_id,
                        "rel": str(first_value(rel, ["relationshipType", "type", "mif:type"], "relates_to")),
                        "to": mif_to_mpf[str(target)],
                    }
                )
            elif target:
                influences.append({"type": "external_uri", "uri": str(target), "relationship": "mif:relationship"})

        records.append(
            memory_record(
                source_system="mif",
                record_id=mpf_id,
                content=first_value(item, ["content", "mif:content"], item),
                category=str(first_value(item, ["memoryType", "mif:memoryType", "type"], "semantic")),
                subcategory=str(first_value(item, ["namespace", "mif:namespace"], "mif")),
                created=generated,
                updated=first_value(item, ["modified", "dc:modified"], generated),
                owner_id="mif-import",
                namespace=str(first_value(item, ["namespace", "mif:namespace"], "mif")),
                metadata={
                    "mif_read_only": True,
                    "mif_round_trip_key": mif_id,
                    "mif_raw": item,
                },
                valid_start=first_value(temporal, ["validFrom"], generated),
                valid_end=first_value(temporal, ["validUntil"]),
                actor_type="agent",
                actor_id=str(associated),
                activity_type="activity",
                activity_id=str(derived or "mif:read-only-adapter"),
                influences=influences,
                quality_rating=int(float(first_value(prov, ["confidence"], 0.75)) * 100),
            )
        )

    return envelope(
        source_system="mif",
        source_version=source_version,
        records=records,
        relations=relations,
        source_instance="read-only-adapter",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert MIF JSON-LD to MPF v0.2 as a read-only one-way adapter.")
    parser.add_argument("input", help="MIF .memory.json, JSON-LD bundle, JSONL file, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Output MPF JSON path; defaults to stdout")
    parser.add_argument("--source-version", default="0.1.0-draft")
    args = parser.parse_args()
    write_json(convert(load_json(args.input), args.source_version), args.output)


if __name__ == "__main__":
    main()
