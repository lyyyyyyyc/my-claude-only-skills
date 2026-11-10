#!/usr/bin/env python
"""Fail closed unless PyTorch sees the requested Kaggle multi-GPU profile."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone


PROFILES = {
    "t4x2": {"expected_count": 2, "required_name": "T4"},
    "l4x4": {"expected_count": 4, "required_name": "L4"},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--required-name")
    args = parser.parse_args()

    defaults = PROFILES[args.profile]
    expected_count = args.expected_count or defaults["expected_count"]
    required_name = args.required_name or defaults["required_name"]
    result: dict[str, object] = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "expected_count": expected_count,
        "required_name": required_name,
        "ok": False,
    }

    try:
        import torch

        cuda_available = torch.cuda.is_available()
        count = torch.cuda.device_count()
        names = [torch.cuda.get_device_name(index) for index in range(count)] if cuda_available else []
        result.update(
            {
                "torch_version": torch.__version__,
                "cuda_available": cuda_available,
                "device_count": count,
                "gpu_names": names,
            }
        )
        result["ok"] = (
            cuda_available
            and count == expected_count
            and all(required_name.lower() in name.lower() for name in names)
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    try:
        smi = subprocess.run(
            ["nvidia-smi", "-L"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        result["nvidia_smi_exit_code"] = smi.returncode
        result["nvidia_smi_l"] = smi.stdout.strip()
        if smi.stderr.strip():
            result["nvidia_smi_stderr"] = smi.stderr.strip()
    except Exception as exc:
        result["nvidia_smi_error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
