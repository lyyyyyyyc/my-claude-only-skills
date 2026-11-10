#!/usr/bin/env python
"""Merge per-worker seed JSON ledgers without accepting duplicate or missing seeds silently."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


def task_key(record: dict[str, object]) -> tuple[str, int]:
    return (str(record.get("condition", "")), int(record["seed"]))


def format_task_keys(keys: list[tuple[str, int]]) -> list[dict[str, object]]:
    return [{"condition": condition, "seed": seed} for condition, seed in keys]


def load_manifest(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks = payload["tasks"] if isinstance(payload, dict) else payload
    normalized = [item if isinstance(item, dict) else {"seed": item} for item in tasks]
    duplicate = [key for key, count in Counter(task_key(item) for item in normalized).items() if count > 1]
    if duplicate:
        raise ValueError(f"manifest contains duplicate condition/seed tasks: {format_task_keys(duplicate)}")
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--seed-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    expected_tasks = load_manifest(args.seed_manifest)
    expected = {task_key(task) for task in expected_tasks}
    records: list[dict[str, object]] = []
    invalid_files: list[dict[str, str]] = []
    for path in sorted(args.results_root.glob("worker_*/seed_*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["seed"] = int(payload["seed"])
            payload["source_file"] = str(path)
            records.append(payload)
        except Exception as exc:
            invalid_files.append({"source_file": str(path), "error": f"{type(exc).__name__}: {exc}"})

    seen = Counter(task_key(record) for record in records)
    duplicates = sorted(key for key, count in seen.items() if count > 1)
    unexpected = sorted(key for key in seen if key not in expected)
    successful = [record for record in records if record.get("status") == "success"]
    missing = sorted(key for key in expected if key not in seen)
    failures = sorted((record for record in records if record.get("status") != "success"), key=task_key)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for record in records for key in record}) or ["seed", "status", "source_file"]
    for filename, rows in (("seed_results.csv", sorted(records, key=lambda item: item["seed"])), ("failures.csv", failures)):
        target = args.output_dir / filename
        temporary = target.with_suffix(".csv.tmp")
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        temporary.replace(target)

    coverage = {
        "planned_task_count": len(expected),
        "record_count": len(records),
        "successful_task_count": len(successful),
        "failed_record_count": len(failures),
        "missing_tasks": format_task_keys(missing),
        "duplicate_tasks": format_task_keys(duplicates),
        "unexpected_tasks": format_task_keys(unexpected),
        "invalid_files": invalid_files,
        "complete_without_conflicts": not (missing or duplicates or unexpected or invalid_files),
        "all_expected_succeeded": len(successful) == len(expected) and not (missing or duplicates or unexpected or invalid_files),
    }
    target = args.output_dir / "coverage.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    print(json.dumps(coverage, ensure_ascii=False, indent=2))
    return 0 if coverage["all_expected_succeeded"] else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
