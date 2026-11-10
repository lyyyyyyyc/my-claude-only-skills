# Cell-lct Local Workflow

## Before playback

- Confirm the target Illustrator 2026 document is already open.
- Confirm the input SVG is a local, validated vector file.
- Keep the original raster reference untouched and store any manifest beside the generated SVG.
- Use a descriptive `core_claim` or figure purpose so the reconstruction does not invent scientific structure.

## SVG requirements

Use only editable `path`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, and `text` elements supported by the runtime. Convert complex geometry to solid paths before caching. Keep text as live SVG text and record its font, size, color, position, alignment, and paint order.

Do not use `<image>`, gradients, patterns, clipping, masks, meshes, live effects, or unsupported imported objects. These are not silently flattened.

## Playback

Run the cache preparation script once with the validated Python executable:

```powershell
C:\Users\LX\AppData\Local\Programs\Python\Python312\python.exe scripts\prepare_geometry_cache.py --input <master.svg> --output-dir <workdir> --job-id <job>
```

Then run `scripts/run_cell_lct.ps1` with the same SVG and work directory. The script must use the already open Illustrator document and preserve artwork outside the current job group.

## Fidelity reporting

Report whether the result is:

- an exact supplied SVG replay;
- a local structural reconstruction from a raster reference; or
- an illustrative approximation.

For raster reconstruction, list any uncertain text, curves, small symbols, or layer order. Never claim pixel identity unless it was actually verified.
