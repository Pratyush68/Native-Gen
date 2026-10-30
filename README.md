# Native Generation

Photo of a room in, editable 3D scene out. ComfyUI Cloud is the backend; this single HTML page is the front end.
Built for the Comfy Org Open Source Higgsfield challenge (Most Innovative, Open Weights Only).

## Flow
1. **Detect**: SAM 3.1 finds each asset in the room photo (one job per label) and cuts it out.
2. **Refine 2D**: Qwen-Image-Edit 2511 (+ Lightning LoRA) redraws each cutout as one clean, complete object. Optional context text and reference image.
3. **Confirm assets**, then **Layout**: top-down editor (multi-select, marquee, rotate/resize handles, undo/redo, layers/stacking, room size) beside a live 3D view.
4. **Generate meshes**: TRELLIS.2 builds a GLB per asset, placed per the saved layout.
5. Export `layout.json` (positions, sizes, rotations, provenance) for Unreal/Blender.

## Run
Requires Python 3 and a ComfyUI Cloud account with API access.

    python server.py            # paste your Comfy Cloud API key at the hidden prompt
    # open http://localhost:8188
    python server.py --mock     # fake backend for UI testing (needs Pillow)

The key stays in `server.py` (env `COMFY_API_KEY` also works); the page never sees it. Never commit a key.

## Models (all open weights)
SAM 3.1 (SAM License), Qwen-Image-Edit 2511 (Apache-2.0), TRELLIS.2 (check weights licence). Workflows are in `workflows/`.

## Status
Detect, refine, layout editor and 3D view work. Mesh output retrieval from Comfy Cloud is still being fixed.
Sizes are estimated from typical per-category sizes; edit them if known.

## Provenance
Record the input photo's source and licence in the page's licence field; it is written to `layout.json`.

MIT licence (code).
