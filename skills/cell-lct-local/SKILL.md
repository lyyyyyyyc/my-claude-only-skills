---
name: cell-lct-local
description: |-
  Create or reconstruct editable scientific SVG figures locally from a user-provided description or reference analysis, then append the validated vector artwork to the user's already open Adobe Illustrator 2026 document. Use when the user wants Cell-lct-style Illustrator output without Xiaomiao or any external image API.
metadata: {}
---

# Cell-lct Local

This is the local, no-API variant of `cell-lct`. It does not call Xiaomiao, upload reference images, use a remote vectorizer, or claim that a locally redrawn figure is an exact automatic trace of the source image.

## Required routing

- Read [references/workflow.md](references/workflow.md) before a drawing job.
- Read [references/troubleshooting.md](references/troubleshooting.md) before the first job on a machine, after an environment change or failed playback, or whenever the reference and Illustrator artboard may have different aspect ratios.
- Use only the user's already open Illustrator 2026 document. Never launch, focus, resize, close, or replace Illustrator.
- Before drawing, state that this is a local reconstruction and explain any details that cannot be reliably inferred from the reference.
- If the user supplied a raster reference, inspect it locally and create a text/geometry manifest. Do not upload it.

## Local reconstruction workflow

1. Preserve the original reference. Record visible text, approximate positions, colors, dimensions, layer order, arrows, frames, axes, legends, and scientific structures in a local manifest.
2. Before playback, compare the SVG canvas aspect ratio with the active Illustrator artboard. If they differ materially, warn before drawing and use a matching landscape/portrait artboard or a deliberate crop/export plan; do not silently accept a successful export with large whitespace.
3. Reconstruct the figure as an editable SVG using explicit paths, shapes, and live `<text>` elements. Use the user's reference and description as design input, not as evidence that every pixel can be recovered.
4. Keep the SVG flat 2D with solid fills and strokes. Avoid raster `<image>` nodes, gradients, clipping masks, unsupported effects, and text converted to outlines.
5. Validate the SVG with `scripts/validate_vector_svg.py`, validate the manifest when one is produced, and merge any live text before caching.
6. Run `scripts/prepare_geometry_cache.py` exactly once for a new SVG/job. Reuse the cache only when its source hash and playback settings match; otherwise allocate a new job directory instead of overwriting or guessing.
7. Use `C:\Users\LX\AppData\Local\Programs\Python\Python312\python.exe` when available because it has the validated `fontTools 4.61.1`; otherwise stop and report that the geometry dependency is unavailable.
8. Run `scripts/run_cell_lct.ps1` or `scripts/run_cell_lct_direct.ps1` against the validated SVG. Keep one Illustrator connection for the entire playback, use the existing open document, and preserve artwork outside the current job group.
9. Save the Illustrator document and export the final PNG only after all batches complete. Visually inspect the result and report material differences from the reference.

## API and privacy boundary

- No API Key is needed for this skill.
- Do not run `set-xiaomiao-key.ps1`, `xiaomiao.ps1`, or `vectorize-xiaomiao.ps1`.
- Codex's local image understanding may guide the redraw, but it is not a substitute for a remote raster-to-vector service and must not be described as one.
- Do not send image bytes, manifests, or private research figures to an external service.

## Output contract

- Keep the source SVG, manifest, geometry cache, playback state, AI file, and final PNG in a user-approved working directory.
- Use the next available `shibielujingN` basename for generated artifacts via `scripts/allocate_shibielujing_name.py`.
- Return the editable SVG and Illustrator deliverables, plus a concise note about fidelity limits.

## Failure boundaries

- If Illustrator is not already open, stop and ask the user to open it.
- If no target document is open, stop and ask the user to open one.
- If the input SVG contains unsupported elements or a raster node, stop and fix the SVG before playback.
- If a reference feature is ambiguous, preserve uncertainty and ask for clarification rather than inventing scientific content.
