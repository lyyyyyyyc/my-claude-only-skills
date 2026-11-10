#!/usr/bin/env python
"""Compatibility preflight for legacy L4 x4 notebook calls.

New notebooks should use preflight_gpu_profile.py --profile l4x4.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-count", type=int, default=4)
    parser.add_argument("--required-name", default="L4")
    args = parser.parse_args()

    result: dict[str, object] = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_count": args.expected_count,
        "required_name": args.required_name,
        "ok": False,
    }
    try:
        import torch

        count = torch.cuda.device_count()
        names = [torch.cuda.get_device_name(index) for index in range(count)] if torch.cuda.is_available() else []
        result.update(
            {
                "torch_version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "device_count": count,
                "gpu_names": names,
            }
        )
        result["ok"] = (
            torch.cuda.is_available()
            and count == args.expected_count
            and all(args.required_name.lower() in name.lower() for name in names)
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    try:
        smi = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=15, check=False)
        result["nvidia_smi_exit_code"] = smi.returncode
        result["nvidia_smi_l"] = smi.stdout.strip()
    except Exception as exc:
        result["nvidia_smi_error"] = f"{type(exc).__name__}: {exc}"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
