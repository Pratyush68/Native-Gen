# Native Generation: Full Project Brief

Author: Pratyush Raut. Last updated: Nov 2, 2026.
Purpose of this file: a complete, self-contained briefing, so any collaborator or AI assistant can pick up the project with no other context.

## 1. One-line summary
Native Generation turns **one photo of a room into an editable 3D scene**. A vision model finds every object, SAM cuts each out, an image-edit model cleans each cutout, TRELLIS.2 builds a mesh per object, and a layout editor lets you arrange everything before export to Unreal, Blender, Maya or V-Ray. Backend: ComfyUI Cloud. Front end: one HTML page plus a small local Python proxy. Models are open-weights only.

## 2. Links
- GitHub repo (code, workflows, README, GIFs): https://github.com/Pratyush68/Native-Gen
- Overview video, 2:41 (in repo): https://github.com/Pratyush68/Native-Gen/blob/main/media/overview_720p.mp4
- Step GIFs: https://github.com/Pratyush68/Native-Gen/tree/main/media
- ComfyUI workflow graphs: https://github.com/Pratyush68/Native-Gen/tree/main/workflows (`detect_workflow.json`, `mesh_workflow.json`)
- Contest submission folder (README, demo video, code zip, script, captions): https://drive.google.com/drive/folders/10QDtZ0z8EQHSNdazV91fKdFCh0FwCaLY
- Full-quality demo video (22 MB): only on the author's PC (`Downloads\room_builder\demo_video\final\Native_Generation_demo_v3.mp4`). The Drive and GitHub copies are compressed.
- Contest: Comfy Org "Open Source Higgsfield" challenge (category: Most Innovative / Open Weights Only).

## 3. The idea and why it matters
- Generating one 3D asset from one prompt is a solved demo. A *scene* is harder: objects must be separate, editable, replaceable and placed with correct scale.
- Design thesis carried across the author's work: **"authored control, generated surface"**. The human (or the engine) owns layout, scale, camera and lighting; generative AI owns surface and asset identity.
- Every stage is a ComfyUI workflow, so any model can be swapped without changing the rest of the chain. This is the composable, node-based idea the project explores.
- Ethical-AI positioning: open-weights models only, and each asset keeps source, prompt history and licence in the export (`layout.json`).

## 4. How it started (history)
1. **Earlier work (Sep 2026):** an in-engine "Native-Gen" tool, a custom Unreal Editor panel that sends a concept image to a local ComfyUI + TRELLIS.2 backend and auto-imports the resulting textured GLB into the Content Browser in under three minutes. Fully local (RTX 3070, 8 GB VRAM). Hunyuan3D failed (Python 3.13 wheels, VRAM limits) and Pixal3D was parked (NATTEN on Windows). TRELLIS.2 GGUF worked.
2. **Related earlier research:** "Colour-Addressed Asset Generation": flat-coloured proxy blocks in UE5 lock layout, camera and lighting. Block-to-asset replacement is done on a still first, then the still anchors a video model. Single-stage video replacement failed; the two-stage version worked.
3. **Idea for the scene-level version:** a bigger Native-Gen where a room photo (originally two sides of a room) becomes a top-down asset map and then a full 3D environment with every asset editable.
4. **Oct 28, 2026:** decided to enter Comfy Org's Open Source Higgsfield competition (deadline Fri Oct 30, 9 AM PT). Chose ComfyUI as the backend and an HTML page as the front end, using the author's personal Comfy Cloud subscription.
5. **Oct 30, 2026:** built and committed the whole app in one day (see section 8), created the public repo, and submitted the Typeform entry **a few minutes after the 9 AM PT cutoff**. The author reports upload trouble on his laptop, then switching devices, and says he discussed the timing with Comfy reps at the Culver City event. Eligibility is for the organisers to decide. A note to that effect is in the Drive folder README.
6. **Oct 31, 2026:** re-edited the demo video (v3, narrated, smooth zooms at button clicks, model names and workflows shown, virtual-production ending), uploaded the Drive folder, and added GIFs, the overview video, the walkthrough and a future-scope section to the repo README. The video and some code were updated after the cutoff, and the Drive README says so.

## 5. How it works (pipeline)
| # | Step | Detail | Model |
|---|---|---|---|
| 1 | Detect assets | A vision-language model reads the photo and writes the list of objects; the list is editable. | Qwen 3.5 (with fallbacks) |
| 2 | Crop assets | One SAM job per label cuts out each object. Boxes are colour-coded on the photo and linked to the cutouts. You can add, move, resize, rename, delete, restore. | SAM 3.1 |
| 3 | Refine 2D | Each cutout is redrawn as one clean, complete object (for example "keep only the table"), so the mesh generator gets isolated geometry, not clutter. Optional context text and reference image; last 5 versions kept. | Qwen-Image-Edit 2511 + Lightning LoRA |
| 4 | Room structure | SAM finds floor, walls and ceiling; each becomes a flat texture. Window and door openings are drawn on a wall and hollowed out in 3D. Wall-mounted items can be kept as objects or baked into the wall. | SAM 3.1 + Qwen-Image-Edit |
| 5 | Layout | Top-down editor (multi-select, marquee, rotate/resize handles, snapping, undo/redo, layers) beside a live 3D view with a move/rotate/scale gizmo, height lift and room size. Walls are draggable lines; the floor is a movable block. | in-browser |
| 6 | Meshes | A GLB per asset, placed per the saved layout. | TRELLIS.2 (54-node graph) |
| 7 | Export | `layout.json` with positions, sizes, rotations and provenance. | |

Architecture: browser page (`index.html`, about 500 lines) -> local Python proxy (`server.py`, about 130 lines; holds the Comfy API key, which the page never sees) -> ComfyUI Cloud API. The key is read from a git-ignored `key.txt` or the `COMFY_API_KEY` environment variable.

## 6. How to run
    python server.py            # paste your Comfy Cloud API key at the hidden prompt
    # open http://localhost:8188
    python server.py --mock     # fake backend for UI testing (needs Pillow)
Requires Python 3 and a ComfyUI Cloud account with API access. Windows shortcut: `start.bat`.

## 7. Status and known limits (as of Nov 2, 2026)
- **Confirmed working:** layout editor and live 3D view.
- **Built but not fully verified on real Comfy Cloud:** detect (the Qwen 3.5 text-generation step has not been tested there; the code falls back through Qwen 3.5 4B, 9B, then Qwen2.5-VL), crop, refine, room structure.
- **Not verified:** mesh step. Mesh output retrieval from Comfy Cloud was still being fixed at the last commit. Do not claim the pipeline is proven end to end.
- Sizes are estimated from typical per-category sizes; edit them if known.
- Not built yet: one-click GLB scene export, detecting items on or inside furniture, optional wall perspective flatten, undo/restore for walls and openings, real-world scale from a reference object.
- TRELLIS.2 weights licence should be checked before commercial use.
- Security: a Comfy API key was exposed during development; revoke and rotate it.

### Workflow files in the repo
Only two graphs are exported as JSON in `workflows/`: `detect_workflow.json` (SAM3_Detect, crop by boxes, background removal) and `mesh_workflow.json` (54-node TRELLIS.2 chain). The other stages are ComfyUI graphs built in code inside `index.html` and submitted to Comfy Cloud: the Qwen 3.5 detection graph, and the Qwen-Image-Edit 2511 refine graph (UNETLoader + Lightning LoRA 4-step, TextEncodeQwenImageEditPlus, KSampler). Room-structure detection reuses the SAM graph and its refine reuses the Qwen-Image-Edit graph. So every stage is a ComfyUI graph, but only two have standalone JSON exports so far. Exporting the rest is an easy to-do.

## 8. Build log (git history, all Oct 30 unless noted)
Photo to editable 3D room (initial) -> colour-coded editable detection boxes -> box editing, duplicate filter -> show/restore unticked boxes -> 3D layout gizmo with snapping -> per-asset prompt and regenerate with version history -> TRELLIS graph fix -> room structure (floor/walls/ceiling, openings) -> flat wall textures -> two-step input (Detect assets then Crop assets) -> keep/remove wall-mounted toggle -> key from `key.txt` + `start.bat` -> Qwen 3.5 for detection (Qwen2.5-VL TextGenerate errors on Cloud) -> Oct 31: README, GIFs, overview video.

## 9. Demo video (v3, 2:41), scene order
Intro and left panel -> upload and Detect assets (Qwen 3.5) -> Crop assets with SAM 3.1 (boxes over photo, click a box to select) -> Add box and "keep only the wooden table" with Qwen-Image-Edit, and why it matters -> room structure -> ComfyUI workflow graphs -> layout editor (move, rotate, resize) -> generate meshes with TRELLIS.2 -> virtual-production ending (Unreal, Blender, Maya, V-Ray).

## 10. Future scope
- **Engines and DCCs:** one-click GLB or USD export plus `layout.json`; an Unreal Python/Blueprint importer that spawns each mesh at its saved transform; a Blender add-on doing the same. Same data feeds Maya or V-Ray for archviz.
- **Virtual production:** photograph a location or set and get a blocked-out digital twin in minutes for previs, LED-volume backdrops and camera planning.
- **AI video:** render the layout as depth, normal and segmentation passes for a video model so camera moves match real geometry; per-object masks allow re-styling one asset only.
- **Simulation and robotics:** labeled, metric-sized scenes as quick environments for physics sims, navigation tests and synthetic data. Related earlier idea (MechTwin): layout and worker-path simulation for industrial and entertainment sets.
- **Games and XR:** user-made rooms as playable levels; AR placement of a scanned room.
- **Closed asset loop (from earlier work):** proxy-block transforms already encode scale, position and rotation, so each iteration swaps a block for a real mesh and leaves less for AI to invent.
- **Provenance:** keep per-asset model, version and licence in every export so the chain is auditable.

## 11. Stack and conventions
ComfyUI / ComfyUI Cloud, SAM 3.1, Qwen 3.5, Qwen-Image-Edit 2511 (+ Lightning LoRA), TRELLIS.2, Python, plain HTML/JS, three.js-style 3D view in the page. Downstream targets: Unreal Engine 5, Blender, Maya, V-Ray. Author's local machine: RTX 3070 (8 GB); this project runs its models on Comfy Cloud so VRAM is not a constraint.

## 12. Licences
Code: MIT. SAM 3.1: SAM License. Qwen-Image-Edit 2511: Apache-2.0. TRELLIS.2: check the weights licence.
