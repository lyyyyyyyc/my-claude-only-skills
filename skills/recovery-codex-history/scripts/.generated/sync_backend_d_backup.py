from __future__ import annotations

import importlib.util
import pathlib
import sys

SOURCE = pathlib.Path("C:\\Users\\LX\\.codex-history-sync-tool\\sync_backend.py")
BACKUP_DIR = pathlib.Path("D:\\CodexHistoryBackups")

spec = importlib.util.spec_from_file_location("codex_history_sync_backend", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load backend: {SOURCE}")

backend = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = backend
spec.loader.exec_module(backend)

_original_resolve_paths = backend.resolve_paths


def resolve_paths(codex_home):
    paths = _original_resolve_paths(codex_home)
    paths.backup_dir = BACKUP_DIR
    return paths


backend.resolve_paths = resolve_paths

raise SystemExit(backend.main())
