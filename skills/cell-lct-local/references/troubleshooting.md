# Troubleshooting And Lessons

Use this reference to avoid repeating known setup and playback detours. It records decisions supported by the local reconstruction run on 2026-08-27; it is not a claim that every future job will fail in the same way.

## Problems observed in the run

### 1. Python environment and fontTools did not initially agree

The local geometry cache depends on `fontTools`. The available `D:\python` environment initially reported `fontTools 4.59.0`, while the local Cell-lct runtime was validated against `4.61.1`. This is a real dependency mismatch, not a cosmetic version warning.

Before cache preparation, check the exact interpreter that will run the script:

```powershell
$python = 'C:\Users\LX\AppData\Local\Programs\Python\Python312\python.exe'
& $python -c "import sys, fontTools; print(sys.executable); print(fontTools.__version__)"
```

Use one validated interpreter for cache preparation and do not mix its packages with another Python installation. If the required version is absent, stop before generating a cache and report the missing dependency. Do not fix the problem by changing the SVG parser or bypassing the cache.

### 1.1. Python launcher assumptions caused an avoidable invocation detour

The local runtime needed the concrete Python 3.12 executable rather than relying on a launcher selection flag such as `py -3`. A machine can have several Python installations, and the launcher may select a different environment or be unavailable. Invoke the validated executable by its absolute path, then print `sys.executable` and `fontTools.__version__` before cache preparation. Keep that same interpreter for every Python helper in the job.

### 2. The remote/API workflow was the wrong execution mode

The original `cell-lct` workflow expects Xiaomiao-related remote vectorization, but this skill is explicitly the local no-API variant. For this skill, do not look for an API key, call remote vectorization scripts, or upload a private reference. Codex may inspect the raster locally and redraw its visible structure, but that does not make the result an automatic pixel-level trace.

### 3. A successful Illustrator playback can still produce a poor deliverable

The reconstructed SVG used a wide `1600x684` canvas, while the open Illustrator document used a portrait A4 artboard. All 204 objects and all five playback batches completed, but the exported `595x842` PNG contained substantial whitespace and made the figure appear too small.

Therefore, “all batches completed” is only a structural success check. Before playback, compare canvas and artboard orientation and usable area. If the mismatch is material, pause for an artboard/export decision. Never silently resize, crop, or alter the user's document because the skill must preserve the existing Illustrator file.

## Rules that prevent repeated detours

- Check that Illustrator 2026 is already open and that a target document is open before starting. The skill may connect to the existing application but must not launch, focus, resize, close, or replace it.
- Use a new `shibielujingN` job name and a user-approved output directory. Do not overwrite a previous SVG, cache, AI file, or PNG while experimenting with a new reconstruction.
- Validate the SVG before preparing the cache. Unsupported elements, raster image nodes, dashed strokes, unsupported effects, or outlined text must be corrected in the new SVG rather than silently flattened by the playback script.
- Keep live text where possible and record font family, size, color, position, alignment, and paint order in the manifest. If a glyph or font is uncertain, report it instead of inventing a scientific label.
- Use one Illustrator connection for all batches. If playback is interrupted, inspect `playback.json`; resume only with the same source hash, cache, job ID, and settings. Do not rebuild a compatible cache just to retry.

## Failure classification

| Observation | Meaning | Required response |
|---|---|---|
| `fontTools` version is below the validated requirement | Environment blocker | Stop cache preparation and use the validated interpreter/environment |
| Cache/state exists but source hash or settings differ | Stale job state | Allocate a new job directory; do not overwrite the old state |
| SVG validation rejects an element | Input-format blocker | Replace the unsupported element with supported editable geometry |
| Illustrator is closed or has no target document | Application precondition missing | Ask the user to open Illustrator and the target document |
| Playback succeeds but PNG has excessive whitespace or tiny content | Artboard/output mismatch | Fix the artboard or choose a deliberate crop/export plan, then inspect again |
| Text, symbols, arrows, or layer order cannot be inferred | Reference ambiguity | Preserve the uncertainty and ask for clarification; do not fabricate content |

## What this reference does not require

These lessons do not require installing Xiaomiao, changing the original `cell-lct` skill, automatically modifying the user's Illustrator artboard, or claiming pixel identity for a raster reconstruction. They are preflight and recovery rules for the local variant.
