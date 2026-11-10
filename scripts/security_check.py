"""Scan files and accept only manually reviewed examples bound to exact file hashes."""

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gitleaks", default="gitleaks")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    repo = args.repo.resolve()
    reviewed = json.loads((repo / "_meta/security-reviewed-examples.json").read_text(encoding="utf-8"))
    accepted = {
        (entry["path"], entry["rule"], entry["startLine"], entry["endLine"], entry["fileSha256"])
        for entry in reviewed["examples"]
    }
    with tempfile.TemporaryDirectory(prefix="skill-security-", dir=repo.parent) as scratch:
        report = Path(scratch) / "findings.json"
        result = subprocess.run([
            args.gitleaks, "dir", str(repo), "--redact=100", "--report-format", "json",
            "--report-path", str(report), "--no-banner", "--max-target-megabytes", "20",
            "--log-level", "error",
        ], capture_output=True, text=True, encoding="utf-8")
        if result.returncode not in (0, 1) or not report.is_file():
            print(json.dumps({"scanError": True, "exitCode": result.returncode}))
            return 2
        findings = json.loads(report.read_text(encoding="utf-8"))
        unknown = []
        for finding in findings:
            file = Path(finding["File"]).resolve()
            relative = file.relative_to(repo).as_posix()
            file_hash = hashlib.sha256(file.read_bytes()).hexdigest()
            key = (relative, finding["RuleID"], finding["StartLine"], finding["EndLine"], file_hash)
            if key not in accepted:
                unknown.append({
                    "path": relative, "rule": finding["RuleID"],
                    "startLine": finding["StartLine"], "endLine": finding["EndLine"],
                })
        print(json.dumps({
            "findings": len(findings), "reviewedExamples": len(findings) - len(unknown),
            "unreviewedFindings": unknown,
        }, indent=2))
        return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
