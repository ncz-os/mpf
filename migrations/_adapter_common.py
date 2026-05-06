#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_utc(value: Any, default: str | None = None) -> str | None:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).replace(
            microsecond=0
        ).isoformat().replace("+00:00", "Z")
    if not isinstance(value, str):
        return default
    text = value.strip()
    if not text:
        return default
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return f"{text}T00:00:00Z"
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return default
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def load_json(path: str) -> Any:
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    if path.endswith(".jsonl"):
        return [json.loads(line) for line in stripped.splitlines() if line.strip()]
    return json.loads(stripped)


def write_json(data: Any, path: str | None = None) -> None:
    text = json.dumps(data, indent=2, sort_keys=False) + "\n"
    if path:
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def get_path(obj: Any, path: str, default: Any = None) -> Any:
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def first_value(obj: dict[str, Any], paths: list[str], default: Any = None) -> Any:
    for path in paths:
        value = get_path(obj, path)
        if value is not None and value != "":
            return value
    return default


def list_from(data: Any, keys: list[str]) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in keys:
        value = get_path(data, key)
        if isinstance(value, list):
            return value
    return []


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(json.dumps(part, sort_keys=True, default=str) for part in parts)
    digest = sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, sort_keys=True, default=str)


def compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if v is not None}


def provenance(
    *,
    source_system: str,
    generated_at: str,
    actor_type: str = "system",
    actor_id: str | None = None,
    activity_type: str = "etl_job",
    activity_id: str | None = None,
    influences: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "wasAttributedTo": {
            "type": actor_type,
            "id": actor_id or f"system:{source_system}",
        },
        "wasGeneratedBy": {
            "type": activity_type,
            "id": activity_id or f"{source_system}:adapter-import",
        },
        "wasInfluencedBy": influences or [],
        "generatedAtTime": generated_at,
    }


def memory_record(
    *,
    source_system: str,
    record_id: str,
    content: Any,
    category: str,
    subcategory: str = "import",
    created: Any = None,
    updated: Any = None,
    owner_id: str = "imported",
    namespace: str = "default",
    metadata: dict[str, Any] | None = None,
    valid_start: Any = None,
    valid_end: Any = None,
    actor_type: str = "system",
    actor_id: str | None = None,
    activity_type: str = "etl_job",
    activity_id: str | None = None,
    influences: list[dict[str, Any]] | None = None,
    quality_rating: int = 75,
) -> dict[str, Any]:
    created_at = iso_utc(created, now_utc())
    updated_at = iso_utc(updated, created_at)
    valid_from = iso_utc(valid_start, created_at)
    valid_until = iso_utc(valid_end) if valid_end else None
    body = clean_text(content)
    return {
        "id": record_id,
        "kind": "memory",
        "payload_version": "mnemos-3.1",
        "valid_time_start": valid_from,
        "valid_time_end": valid_until,
        "transaction_time": created_at,
        "provenance": provenance(
            source_system=source_system,
            generated_at=created_at,
            actor_type=actor_type,
            actor_id=actor_id,
            activity_type=activity_type,
            activity_id=activity_id,
            influences=influences,
        ),
        "payload": {
            "content": body,
            "category": category,
            "subcategory": subcategory,
            "created": created_at,
            "updated": updated_at,
            "owner_id": owner_id,
            "namespace": namespace,
            "permission_mode": 600,
            "quality_rating": quality_rating,
            "metadata": metadata or {},
        },
    }


def event_record(
    *,
    source_system: str,
    record_id: str,
    event_type: str,
    content: Any,
    occurred_at: Any = None,
    session_id: str | None = None,
    actor: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = iso_utc(occurred_at, now_utc())
    return {
        "id": record_id,
        "kind": "event",
        "payload_version": "mpf-0.1",
        "transaction_time": timestamp,
        "provenance": provenance(
            source_system=source_system,
            generated_at=timestamp,
            actor_type="system",
            actor_id=f"system:{source_system}",
            activity_type="etl_job",
        ),
        "payload": compact_dict({
            "event_type": event_type,
            "session_id": session_id,
            "actor": actor,
            "content": clean_text(content),
            "occurred_at": timestamp,
            "metadata": metadata or {},
        }),
    }


def fact_record(
    *,
    source_system: str,
    record_id: str,
    statement: Any,
    created: Any = None,
    subject: str | None = None,
    predicate: str | None = None,
    object_value: str | None = None,
    confidence: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timestamp = iso_utc(created, now_utc())
    payload: dict[str, Any] = {
        "statement": clean_text(statement),
        "created": timestamp,
        "metadata": metadata or {},
    }
    if subject:
        payload["subject"] = subject
    if predicate:
        payload["predicate"] = predicate
    if object_value:
        payload["object"] = object_value
    if confidence is not None:
        payload["confidence"] = max(0.0, min(1.0, float(confidence)))
    return {
        "id": record_id,
        "kind": "fact",
        "payload_version": "mpf-0.1",
        "transaction_time": timestamp,
        "provenance": provenance(
            source_system=source_system,
            generated_at=timestamp,
            actor_type="system",
            actor_id=f"system:{source_system}",
            activity_type="etl_job",
        ),
        "payload": payload,
    }


def envelope(
    *,
    source_system: str,
    source_version: str,
    records: list[dict[str, Any]],
    kg_triples: list[dict[str, Any]] | None = None,
    relations: list[dict[str, Any]] | None = None,
    source_instance: str | None = None,
    exported_at: Any = None,
) -> dict[str, Any]:
    env: dict[str, Any] = {
        "mpf_version": "0.2.0",
        "source_system": source_system,
        "source_version": source_version,
        "exported_at": iso_utc(exported_at, now_utc()),
        "record_count": len(records),
        "records": records,
    }
    if source_instance:
        env["source_instance"] = source_instance
    if kg_triples:
        env["kg_triples"] = kg_triples
    if relations:
        env["relations"] = relations
    return env
