#!/usr/bin/env python3
"""
validate.py — validate MPF envelopes against the matching versioned schema.

Standalone. Any memory system (Mem0, Letta, Graphiti, Cognee, MNEMOS,
MemPalace) can use this to validate its own MPF emissions before
shipping them. The schema file it validates against is the authoritative
wire-format definition.

Usage:
  python validate.py vectors/                      # validate every *.json vector
  python validate.py export.json
  python validate.py --file export.json
  python validate.py --file - < export.json        # stdin
  python validate.py export.json --schema schema/mpf-v0.2.json

Exit codes:
  0 — envelope validates
  1 — validation failed (prose error list printed to stderr)
  2 — I/O or schema-load error

Depends on the `jsonschema` package (pip install jsonschema). Falls
back to structural-only checks if jsonschema isn't installed so the
tool still catches gross shape errors in a dependency-minimal
environment.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent
SCHEMA_BY_VERSION = {
    "0.1": REPO_ROOT / "schema" / "mpf-v0.1.json",
    "0.2": REPO_ROOT / "schema" / "mpf-v0.2.json",
}


def _load_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _version_key(env: Any) -> Optional[str]:
    if not isinstance(env, dict):
        return None
    version = env.get("mpf_version")
    if not isinstance(version, str):
        return None
    match = re.match(r"^(0\.[0-9]+)(?:\.[0-9]+)?$", version)
    return match.group(1) if match else None


def _schema_path_for_env(env: Any) -> Optional[Path]:
    version = _version_key(env)
    if version is None:
        return None
    return SCHEMA_BY_VERSION.get(version)


def _parse_utc_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.utcoffset() != timedelta(0):
        return None
    return parsed


def _check_utc_datetime(errs: List[str], value: Any, loc: str) -> Optional[datetime]:
    parsed = _parse_utc_datetime(value)
    if parsed is None:
        errs.append(f"{loc} must be an ISO-8601 UTC date-time")
    return parsed


def _structural_check_v0_2(env: Dict[str, Any], records: List[Any]) -> List[str]:
    errs: List[str] = []
    record_ids = {
        rec.get("id")
        for rec in records
        if isinstance(rec, dict) and isinstance(rec.get("id"), str)
    }

    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            continue

        valid_start = rec.get("valid_time_start")
        valid_end = rec.get("valid_time_end")
        transaction_time = rec.get("transaction_time")
        parsed_start: Optional[datetime] = None
        parsed_end: Optional[datetime] = None

        if valid_start is not None:
            parsed_start = _check_utc_datetime(
                errs, valid_start, f"records[{i}].valid_time_start"
            )
        if valid_end is not None:
            parsed_end = _check_utc_datetime(
                errs, valid_end, f"records[{i}].valid_time_end"
            )
        if parsed_start is not None and parsed_end is not None and parsed_end < parsed_start:
            errs.append(f"records[{i}].valid_time_end must not be before valid_time_start")
        if transaction_time is not None:
            _check_utc_datetime(errs, transaction_time, f"records[{i}].transaction_time")

        if rec.get("kind") != "memory":
            continue

        provenance = rec.get("provenance")
        if not isinstance(provenance, dict):
            errs.append(f"records[{i}] kind='memory' missing required object: 'provenance'")
            continue

        generated_at = provenance.get("generatedAtTime")
        if generated_at is None:
            errs.append(f"records[{i}].provenance missing required field: 'generatedAtTime'")
        else:
            _check_utc_datetime(
                errs, generated_at, f"records[{i}].provenance.generatedAtTime"
            )

        attributed = provenance.get("wasAttributedTo")
        if not isinstance(attributed, dict):
            errs.append(f"records[{i}].provenance.wasAttributedTo must be an object")
        else:
            if attributed.get("type") not in {"agent", "user", "system"}:
                errs.append(
                    f"records[{i}].provenance.wasAttributedTo.type must be "
                    "agent, user, or system"
                )
            if not isinstance(attributed.get("id"), str) or not attributed.get("id"):
                errs.append(f"records[{i}].provenance.wasAttributedTo.id must be a string")

        generated_by = provenance.get("wasGeneratedBy")
        if not isinstance(generated_by, dict):
            errs.append(f"records[{i}].provenance.wasGeneratedBy must be an object")
        else:
            allowed = {"chat_session", "etl_job", "federation_pull", "distillation", "activity"}
            if generated_by.get("type") not in allowed:
                errs.append(
                    f"records[{i}].provenance.wasGeneratedBy.type must be one of "
                    f"{', '.join(sorted(allowed))}"
                )
            if not isinstance(generated_by.get("id"), str) or not generated_by.get("id"):
                errs.append(f"records[{i}].provenance.wasGeneratedBy.id must be a string")

        influences = provenance.get("wasInfluencedBy", [])
        if not isinstance(influences, list):
            errs.append(f"records[{i}].provenance.wasInfluencedBy must be an array")
            continue
        for j, influence in enumerate(influences):
            loc = f"records[{i}].provenance.wasInfluencedBy[{j}]"
            if not isinstance(influence, dict):
                errs.append(f"{loc} must be an object")
                continue
            influence_type = influence.get("type")
            if influence_type == "memory":
                target_id = influence.get("id")
                if not isinstance(target_id, str) or not target_id:
                    errs.append(f"{loc}.id must be a string when type='memory'")
                elif target_id not in record_ids:
                    errs.append(f"{loc}.id references unknown record id {target_id!r}")
                elif target_id == rec.get("id"):
                    errs.append(f"{loc}.id must not reference its own record")
            elif influence_type == "external_uri":
                if not isinstance(influence.get("uri"), str) or not influence.get("uri"):
                    errs.append(f"{loc}.uri must be a string when type='external_uri'")
            else:
                errs.append(f"{loc}.type must be memory or external_uri")
    return errs


def _structural_check(env: Any) -> List[str]:
    """Minimal shape check that runs even without jsonschema installed.

    Covers the required-fields rules in the spec so a missing
    jsonschema dependency doesn't turn the validator into a no-op.
    """
    errs: List[str] = []
    if not isinstance(env, dict):
        return ["envelope must be a JSON object"]
    for k in ("mpf_version", "exported_at", "records"):
        if k not in env:
            errs.append(f"envelope missing required field: {k!r}")
    records = env.get("records")
    if records is not None and not isinstance(records, list):
        errs.append("'records' must be an array")
        return errs
    for i, rec in enumerate(records or []):
        if not isinstance(rec, dict):
            errs.append(f"records[{i}] is not an object")
            continue
        for k in ("id", "kind", "payload_version", "payload"):
            if k not in rec:
                errs.append(f"records[{i}] missing required field: {k!r}")
    # Record-id uniqueness (critical round-trip invariant)
    seen: Dict[str, int] = {}
    for i, rec in enumerate(records or []):
        if not isinstance(rec, dict):
            continue
        rid = rec.get("id")
        if not isinstance(rid, str):
            continue
        if rid in seen:
            errs.append(
                f"records[{i}] duplicate id {rid!r} "
                f"(already seen at records[{seen[rid]}])"
            )
        else:
            seen[rid] = i
    if _version_key(env) == "0.2":
        errs.extend(_structural_check_v0_2(env, records or []))
    return errs


def _full_check(env: Any, schema: Any) -> List[str]:
    """Run the full JSON Schema validation via the jsonschema package."""
    try:
        from jsonschema.validators import Draft202012Validator
    except ImportError:
        return []
    try:
        validator = Draft202012Validator(schema)
    except Exception as exc:
        return [f"schema load error: {exc}"]
    errs: List[str] = []
    for e in sorted(validator.iter_errors(env), key=lambda x: list(x.path)):
        loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
        errs.append(f"{loc}: {e.message}")
    return errs


def validate(env: Any, schema: Optional[Any]) -> List[str]:
    """Run structural + full schema checks. Structural always runs; full
    runs only when jsonschema is installed and a schema was loaded."""
    errs = _structural_check(env)
    # Avoid duplicating structural errors when full-schema would catch
    # the same thing; run full-schema only if structural passed.
    if not errs and schema is not None:
        errs.extend(_full_check(env, schema))
    return errs


def summary(env: Any) -> str:
    if not isinstance(env, dict):
        return "(not an envelope)"
    records = env.get("records") or []
    by_kind: Dict[str, int] = {}
    for rec in records:
        if isinstance(rec, dict):
            k = rec.get("kind", "<missing>")
            by_kind[k] = by_kind.get(k, 0) + 1
    sidecar_counts = {
        k: len(env.get(k) or [])
        for k in ("kg_triples", "relations", "compression_manifest",
                  "memory_versions", "deletion_log", "attestations")
        if env.get(k)
    }
    parts = [
        f"mpf_version={env.get('mpf_version')!r}",
        f"source_system={env.get('source_system')!r}",
        f"records={len(records)}",
    ]
    if by_kind:
        parts.append("kinds=" + ",".join(f"{k}:{v}" for k, v in sorted(by_kind.items())))
    if sidecar_counts:
        parts.append("sidecars=" + ",".join(f"{k}:{v}" for k, v in sidecar_counts.items()))
    return " ".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mpf-validate",
        description=(
            "Validate MPF envelopes against the matching schema. The schema "
            "files are authoritative; this tool is a convenience runner."
        ),
    )
    parser.add_argument("path", nargs="?", metavar="PATH",
                        help="Path to an envelope JSON file or directory of *.json files")
    parser.add_argument("--file", metavar="PATH",
                        help="Path to envelope JSON file, or '-' for stdin")
    parser.add_argument("--schema", metavar="PATH",
                        help="Override schema path instead of auto-selecting by mpf_version")
    parser.add_argument("--quiet", action="store_true",
                        help="Only print errors; no summary line")
    parser.add_argument("--no-schema", action="store_true",
                        help="Skip full JSON Schema check; run structural only")
    args = parser.parse_args(argv)

    target = args.file or args.path
    if target is None:
        parser.error("provide PATH or --file PATH")

    if target == "-":
        targets = [target]
    else:
        target_path = Path(target)
        if target_path.is_dir():
            targets = [str(p) for p in sorted(target_path.glob("*.json"))]
        else:
            targets = [target]

    if not targets:
        print(f"ERROR no *.json files found in {target}", file=sys.stderr)
        return 2

    total_errors = 0
    for target_file in targets:
        try:
            env = _load_json(target_file)
        except Exception as exc:
            print(f"ERROR reading {target_file}: {exc}", file=sys.stderr)
            return 2

        schema: Optional[Any] = None
        if not args.no_schema:
            schema_path: Optional[Path]
            if args.schema:
                schema_path = Path(args.schema)
            else:
                schema_path = _schema_path_for_env(env)
            if schema_path is None:
                version = env.get("mpf_version") if isinstance(env, dict) else None
                print(f"ERROR no schema registered for mpf_version={version!r}", file=sys.stderr)
                return 2
            try:
                schema = _load_json(str(schema_path))
            except Exception as exc:
                print(f"ERROR loading schema {schema_path}: {exc}", file=sys.stderr)
                return 2

        errs = validate(env, schema)

        prefix = "" if target_file == "-" else f"{target_file}: "
        if not args.quiet:
            print(prefix + summary(env), file=sys.stderr)

        if errs:
            total_errors += len(errs)
            print(prefix + f"VALIDATION FAILED ({len(errs)} error(s)):", file=sys.stderr)
            for e in errs:
                print(f"  {e}", file=sys.stderr)
        elif not args.quiet:
            print(prefix + "OK", file=sys.stderr)

    if total_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
