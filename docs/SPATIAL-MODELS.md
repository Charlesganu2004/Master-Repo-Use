# Spatial Models

Everything in this catalog that turns images, video, depth or range data into geometry, spatial
understanding, or a live map. Three sub-lanes: offline-leaning 3D reconstruction and scene
representation, spatial-reasoning VLMs and world models, and AR/robotics mapping and SLAM. This is
the lane guide for [Scout](../agents/spatial-scout.md), and it is organised around the five things
Scout must establish before recommending anything: input, output, latency class, hardware ceiling,
and commercial use.

**The warning that governs this entire lane: the code license and the weights license routinely
differ.** A repo whose GitHub badge says Apache-2.0 can ship checkpoints that are non-commercial,
research-only, or governed by an upstream base-model license the repo never mentions on its front
page. In this field that is the norm, not the exception. Never quote a single license for a
model repo without naming which artifact it applies to. Every entry below states code and weights
separately wherever they diverge, and [License traps](#license-traps) collects the ones that will
actually bite.

Related:
- [agents/spatial-scout.md](../agents/spatial-scout.md) — the agent this doc serves
- [VETTING-REPORT.md](VETTING-REPORT.md) — what was rejected and why
- [SECURITY-SCANNING.md](SECURITY-SCANNING.md) — the pipeline every entry here passed
- [skills/dep-audit](../skills/dep-audit/SKILL.md) — run this before adding anything not listed here

---

## Latency classes used in this doc

| Class | Means | Example |
|---|---|---|
| Offline | Batch job, minutes to hours, no human waiting | COLMAP dense reconstruction |
| Interactive | Seconds per operation, human in the loop, viewport responds | Splat editing, feed-forward inference on a clip |
| Hard real-time | Keeps up with a live camera or LiDAR feed on a fixed per-frame budget | VIO, LiDAR SLAM, splat rasterisation |

"Real-time" as printed in a README is a claim about some resolution on some GPU with some number
of input frames. This catalog does not carry measured frame rates or VRAM figures, because none
were independently benchmarked here. Treat the hardware column as a class, not a number, and
verify against the user's actual GPU before promising a latency budget.

---

## How to choose

Keyed on what you have and what you need out.

| You have | You need | Start with | Latency class |
|---|---|---|---|
| Unposed photos, many, quality matters | Poses + dense mesh | [colmap/colmap](https://github.com/colmap/colmap) | Offline |
| Unposed photos, few, or SfM already failed | Poses + point maps + depth, one forward pass | [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | Interactive |
| Mixed inputs (images, some poses, some depth) | Geometry in metres | [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) | Interactive |
| Any view count, want a streaming-capable model | Consistent depth/geometry | [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Interactive to real-time |
| Posed images and want a photoreal renderable scene | Gaussian splats | [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) or [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | Offline train, real-time render |
| A splat file someone else made | Clean, crop, compress, publish | [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | Interactive |
| Live mono/stereo/RGB-D camera | Poses + sparse map, robust | [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | Hard real-time |
| Camera + IMU, need drift-free odometry | State estimate | [rpng/open_vins](https://github.com/rpng/open_vins) | Hard real-time |
| LiDAR, with or without IMU | Trajectory + global map | [koide3/glim](https://github.com/koide3/glim) | Hard real-time |
| RGB-D or LiDAR, need a planner-ready volume | TSDF/ESDF distance field | [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | Hard real-time |
| Live sensors, need semantics not just geometry | 3D scene graph | [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) | Hard real-time |
| An image and a language instruction | A point to act on | [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | Interactive |
| A robot and a language instruction | An action chunk | [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | Interactive |
| Video and a need to predict what happens next | Latent world state | [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) | Interactive |

Text version of the same decision, for the common case:

```
What is the input?
├── Images, no poses
│   ├── Hundreds, quality > speed, no GPU budget ......... COLMAP  (offline, CPU/GPU, BSD-3)
│   ├── Few, or SfM already failed on them .............. VGGT    (custom Meta license — check weights)
│   └── Need metres, not arbitrary scale ................ MapAnything (weights CC-BY-NC by default)
├── Video / any-view, want streaming
│   └── ................................................. Depth-Anything-3 (S/B/L Apache; Giant restricted)
├── Posed images, want a renderable scene
│   ├── Train + edit natively, GPL is acceptable ........ LichtFeld-Studio (GPL-3.0)
│   ├── Need a library inside your own trainer .......... gsplat (Apache-2.0)
│   └── Only viewing/cleaning an existing splat ......... SuperSplat (MIT)
├── Live camera
│   ├── Sparse, proven, permissive ...................... stella_vslam (BSD-2)
│   ├── Camera + IMU, and GPL is acceptable ............. OpenVINS (GPL-3.0)
│   └── Dense learned prior, research only .............. MASt3R-SLAM (CC BY-NC-SA — non-commercial)
└── LiDAR / RGB-D
    ├── Trajectory + map ................................ GLIM (MIT)
    ├── Occupancy for planning .......................... nvblox (Apache-2.0 + some BSD-3)
    └── Semantic hierarchy .............................. Hydra (BSD-2)

Commercial product? Delete every non-commercial and copyleft branch above
before you start comparing quality. See "License traps".
```

Rule of order: classical geometry first. If a well-posed SfM problem solves it, COLMAP costs no
VRAM and no license review. Reach for a feed-forward foundation model when poses are unavailable,
views are too few, or the imagery breaks correspondence-based matching.

---

## 3D reconstruction and scene representation

| Repo | Use it when | Fast start | License |
|---|---|---|---|
| [colmap/colmap](https://github.com/colmap/colmap) | You have an ordered or unordered image collection and want the proven SfM + MVS answer with no model weights involved | `colmap automatic_reconstructor --workspace_path W --image_path I` | BSD-3-Clause (GitHub shows NOASSERTION only because of bundled third-party components) |
| [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | You need cameras, depth, point maps and 3D point tracks from 1 to hundreds of unposed images in a single forward pass | `git clone https://github.com/facebookresearch/vggt && pip install -r requirements.txt` | FLAG — custom Meta license, GitHub reports NOASSERTION; the original VGGT-1B checkpoint is research/non-commercial |
| [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) | You need factored **metric** 3D geometry and your inputs are a mix of images, calibration, poses and/or depth across many reconstruction tasks | `git clone https://github.com/facebookresearch/map-anything && pip install -e .` | Apache-2.0 code / FLAG — default released weights are CC-BY-NC 4.0 |
| [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | You want one plain-transformer model that recovers spatially consistent geometry from any number of views, posed or unposed, including streaming use | `git clone https://github.com/ByteDance-Seed/Depth-Anything-3 && pip install -e .` | Apache-2.0 code and Small/Base/Large weights / FLAG — Giant checkpoints are not Apache; read that model card |
| [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) | You want to train, inspect, edit and export 3D Gaussian Splatting scenes in a native app with a real-time viewport | `cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build` | FLAG — GPL-3.0, strong copyleft |
| [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | You already have splats and need to inspect, clean, crop, compress or publish them without installing anything | `https://superspl.at/editor`, or clone and `npm install && npm run develop` | MIT |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | You want a common API across NeRF variants plus data parsers, a web viewer and exporters | `pip install nerfstudio` then `ns-train splatfacto --data DATA` | Apache-2.0 |

Input / output / latency for this section:

| Repo | Input | Output | Latency | Hardware class |
|---|---|---|---|---|
| colmap | Unposed images | Poses, sparse + dense point cloud, mesh | Offline | CPU viable; GPU for dense MVS |
| vggt | 1 to hundreds of unposed images | Cameras, depth, point maps, 3D tracks | Interactive | Single GPU; cost scales with view count |
| map-anything | Images ± calibration ± poses ± depth | Metric 3D geometry, 12+ task heads | Interactive | Single GPU |
| Depth-Anything-3 | Any view count, posed or unposed; monocular through multi-view | Consistent depth / geometry | Interactive, streaming-capable at smaller sizes | Scales by checkpoint size |
| LichtFeld-Studio | Posed images (typically COLMAP output) | Trained splat scene, edited and exported | Offline train, real-time viewport | CUDA GPU required |
| supersplat | Existing splat files | Cleaned/compressed/published splats | Interactive | Browser, no install |
| nerfstudio | Posed images / video | Radiance field or splat, plus exports | Offline train, interactive viewer | CUDA GPU required |

Metric scale note: of this group, **map-anything is the one that advertises metric output**. COLMAP
and most feed-forward pointmap methods are scale-ambiguous without external reference. If the user
needs measurements in metres, say so before recommending anything else here.

---

## Spatial reasoning VLMs and world models

| Repo | Use it when | Fast start | License |
|---|---|---|---|
| [NVIDIA/cosmos](https://github.com/NVIDIA/cosmos) | You want an open platform of world foundation models, datasets and tooling for Physical AI, including the Cosmos 3 omnimodal family (Super 64B, Nano 16B) | `git clone https://github.com/NVIDIA/cosmos` then follow the install docs | FLAG — OpenMDW-1.1 for **both** code and weights; an open model/data license, not a standard OSI permissive license |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | You want reference open VLA models for robot control — π₀ flow-based and π₀-FAST autoregressive | `git clone --recurse-submodules https://github.com/Physical-Intelligence/openpi && uv sync` | Apache-2.0 repo code / FLAG — ships a separate `LICENSE_GEMMA.txt`; PaliGemma/Gemma-derived weights carry Google's terms |
| [allenai/molmoact](https://github.com/allenai/molmoact) | You want a VLA that emits explicit spatial reasoning traces — depth perception tokens and 2D visual trace waypoints — rather than an opaque action head | `git clone https://github.com/allenai/molmoact && pip install -e .` | Apache-2.0 for code **and** weights; README frames it as research/educational, the license itself does not restrict |
| [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) | You want a non-generative video world model that predicts in latent space, for embodied planning rather than pixel synthesis | `git clone https://github.com/facebookresearch/vjepa2 && pip install -e .` | MIT — the cleanest license in this sub-lane |
| [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | You want an interactive, playable world model: controllable explorable video environments with long-horizon memory, streaming in real time | `git clone https://github.com/SkyworkAI/Matrix-Game && pip install -r requirements.txt` | MIT on the repo — FLAG: verify the Hugging Face model card separately, Skywork weight releases do not always match the repo license |
| [FlagOpen/RoboBrain2.5](https://github.com/FlagOpen/RoboBrain2.5) | You want an embodied spatial-reasoning VLM covering spatial perception, affordance and pointing prediction, and trajectory reasoning | `git clone https://github.com/FlagOpen/RoboBrain2.5 && pip install -e .` | Apache-2.0, and the Qwen2.5-VL base is itself Apache-2.0 — unusually clean weight lineage for this lane |
| [remyxai/VQASynth](https://github.com/remyxai/VQASynth) | You need to *generate* spatial VQA training data rather than consume a model — lifts 2D images into metric 3D via depth, segmentation and point clouds | `git clone https://github.com/remyxai/VQASynth && pip install -e .` | Apache-2.0 pipeline / FLAG — generated datasets inherit the terms of your source images and of the depth/segmentation models you run |
| [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | You want a language instruction turned into 2D image keypoints indicating where to act | `git clone https://github.com/wentaoyuan/RoboPoint && pip install -e .` | Apache-2.0 repo / FLAG — built on the LLaVA/Vicuna stack, so released checkpoints inherit Llama community license terms |
| [vision-x-nyu/thinking-in-space](https://github.com/vision-x-nyu/thinking-in-space) | You need to *measure* visual-spatial reasoning rather than ship it — VSI-Bench, 288 real indoor video sequences | `git clone https://github.com/vision-x-nyu/thinking-in-space && pip install -e .` | Apache-2.0 code / FLAG — source videos (ScanNet, ScanNet++, ARKitScenes) carry their own dataset terms |
| [EvolvingLMMs-Lab/lmms-eval](https://github.com/EvolvingLMMs-Lab/lmms-eval) | You want one harness across text, image, video and audio tasks with hundreds of registered benchmarks | `pip install lmms-eval` | Dual: MIT for the core pipeline inherited from lm-evaluation-harness, Apache-2.0 for task and model implementations |

Input / output / latency for this section:

| Repo | Input | Output | Latency | Notes |
|---|---|---|---|---|
| cosmos | Multimodal / video conditioning | Predicted world rollouts, embodied planning signal | Offline to interactive | Large models; datacentre-class for the biggest sizes |
| openpi | Images + language + robot state | Action chunks | Interactive, robot control loop | Weights licensing is the constraint, not compute |
| molmoact | Image + instruction | Reasoning trace, depth tokens, 2D waypoints, actions | Interactive | Traces are inspectable, useful for debugging |
| vjepa2 | Video | Latent predictive state (not pixels) | Interactive | Non-generative; do not expect renderable output |
| Matrix-Game | User control input | Streamed interactive video environment | Real-time streaming (as claimed by the project) | Verify on target GPU |
| RoboBrain2.5 | Image/video + instruction | Spatial perception, affordances, pointing, trajectories | Interactive | Cleanest license in the embodied group |
| VQASynth | Image corpus | Synthetic spatial VQA dataset | Offline batch | Data tool, not an inference model |
| RoboPoint | Image + instruction | 2D keypoints | Interactive | |
| thinking-in-space | Indoor video + QA | Benchmark scores | Offline | Evaluation only |
| lmms-eval | Model + task config | Benchmark scores | Offline | Evaluation only |

Do not present an evaluation harness as a capability. VQASynth, thinking-in-space and lmms-eval
produce data and numbers, not spatial output for a product.

---

## AR / robotics mapping and SLAM

| Repo | Use it when | Fast start | License |
|---|---|---|---|
| [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | You need real-time monocular, stereo or RGB-D visual SLAM with map save/load and a localisation-only mode, under a permissive license | `git clone --recursive https://github.com/stella-cv/stella_vslam` then CMake build | BSD-2-Clause (ships `LICENSE.fork` plus `LICENSE.original` for inherited OpenVSLAM code; GitHub reporting is unreliable here) |
| [rpng/open_vins](https://github.com/rpng/open_vins) | You have a camera plus IMU and need filter-based (MSCKF) visual-inertial odometry with sliding-window estimation and online calibration | Clone into a ROS workspace, then `colcon build` | FLAG — GPL-3.0. Copyleft; linking it into a closed-source AR product is a legal problem |
| [koide3/glim](https://github.com/koide3/glim) | You have LiDAR, with or without IMU, and want GPU-accelerated mapping with global trajectory optimisation | `git clone https://github.com/koide3/glim` then CMake build (ROS 2 wrapper available) | MIT |
| [rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | You want real-time **dense** monocular SLAM using a learned two-view prior, with pointmap fusion and loop closure — research only | `git clone --recursive https://github.com/rmurai0610/MASt3R-SLAM && pip install -e .` | FLAG — CC BY-NC-SA 4.0, **non-commercial**, verified by reading `LICENSE.md`. Also share-alike |
| [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) | You need semantics and hierarchy, not just geometry — objects, places, rooms and buildings as a 3D scene graph built live | Clone into a ROS 2 workspace, then `colcon build` | BSD-2-Clause |
| [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | You need a planner-ready volumetric map — GPU TSDF and ESDF distance fields from RGB-D or LiDAR | `cmake -B build && cmake --build build` (or the Isaac ROS package) | Apache-2.0, with some voxblox-derived files under BSD-3-Clause |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | You need the foundational geometry layer: point clouds, meshes, registration/ICP, RGB-D odometry and integration | `pip install open3d` | MIT (GitHub reports NOASSERTION only because of bundled third-party license files) |
| [borglab/gtsam](https://github.com/borglab/gtsam) | You are building your own SLAM back end and need factor-graph optimisation, batch and incremental (iSAM2), with IMU preintegration | `pip install gtsam` | BSD-3-Clause |
| [rerun-io/rerun](https://github.com/rerun-io/rerun) | You need to see what your pipeline is doing — point clouds, transform trees, images and time series, logged live | `pip install rerun-sdk` then `rerun` | Apache-2.0 (dual MIT OR Apache-2.0) |
| [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | You want CUDA Gaussian splatting rasterisation as a library behind a PyTorch API, inside your own trainer or viewer | `pip install gsplat` | Apache-2.0 — note the contrast with `graphdeco-inria/gaussian-splatting`, which is research/non-commercial |

Input / output / latency for this section:

| Repo | Input | Output | Latency | Hardware class |
|---|---|---|---|---|
| stella_vslam | Mono / stereo / RGB-D camera | Camera trajectory, sparse map, relocalisation | Hard real-time | CPU-feasible |
| open_vins | Camera + IMU | State estimate, calibration | Hard real-time | CPU-feasible |
| glim | LiDAR ± IMU | Trajectory + globally optimised map | Hard real-time | GPU-accelerated |
| MASt3R-SLAM | Monocular camera | Dense pointmaps, trajectory, loop closures | Real-time as claimed by the project | GPU required; verify on target hardware |
| Hydra | Live sensor stream | Hierarchical 3D scene graph | Hard real-time | CPU/GPU, ROS-oriented |
| nvblox | RGB-D or LiDAR | TSDF / ESDF distance fields | Hard real-time | CUDA GPU |
| Open3D | Point clouds, meshes, RGB-D | Processed geometry, registration | Interactive | CPU, optional GPU |
| gtsam | Factors and measurements | Optimised trajectory / map estimate | Real-time capable (iSAM2 is incremental) | CPU |
| rerun | Anything you log | Live visualisation | Hard real-time viewing | CPU/GPU |
| gsplat | Gaussians + camera | Rendered frames, gradients | Real-time rendering | CUDA GPU |

Reconstruction and rendering are different problems. gsplat and supersplat display; COLMAP,
LichtFeld-Studio and nerfstudio produce. Do not recommend a renderer to someone who needs a
reconstruction, or the reverse.

---

## Real-time and live options

The entries that genuinely run against a live camera or LiDAR feed, separated by what "live"
means for each. This is the shortlist when the requirement is a running sensor rather than a
folder of images.

| Repo | Live in what sense | Sensor | Commercial-safe license |
|---|---|---|---|
| [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | Tracks and maps from a live camera stream | Mono / stereo / RGB-D | Yes — BSD-2-Clause |
| [koide3/glim](https://github.com/koide3/glim) | Live LiDAR / LiDAR-inertial mapping with global optimisation | LiDAR ± IMU | Yes — MIT |
| [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | Live volumetric mapping into a planner-consumable distance field | RGB-D / LiDAR | Yes — Apache-2.0 (+ BSD-3 files) |
| [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) | Builds a semantic 3D scene graph incrementally from live sensor data | RGB-D / LiDAR + semantics | Yes — BSD-2-Clause |
| [borglab/gtsam](https://github.com/borglab/gtsam) | Incremental (iSAM2) back end suitable for online estimation | N/A — back end | Yes — BSD-3-Clause |
| [rerun-io/rerun](https://github.com/rerun-io/rerun) | Live streaming visualisation of a running pipeline | Any logged stream | Yes — Apache-2.0 / MIT |
| [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | Real-time rasterisation (rendering, not capture) | N/A — renderer | Yes — Apache-2.0 |
| [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | Real-time in-browser viewing and editing | N/A — viewer | Yes — MIT |
| [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) | Real-time viewport during training and editing | N/A — trainer/editor | **No** for proprietary linking — GPL-3.0 |
| [rpng/open_vins](https://github.com/rpng/open_vins) | Real-time visual-inertial odometry | Camera + IMU | **No** for proprietary linking — GPL-3.0 |
| [rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | Real-time dense monocular SLAM | Monocular camera | **No** — CC BY-NC-SA 4.0, non-commercial |
| [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Streaming-capable geometry from a live view stream | Camera | Yes for S/B/L weights; Giant is flagged |
| [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | Real-time streaming interactive world model | User control input, not a sensor | Repo MIT; weights need checking |

The pattern worth naming: the permissive live stack is sparse and geometric (stella_vslam, GLIM,
nvblox, Hydra, GTSAM), and the licence-encumbered live stack is the dense and learned one
(OpenVINS, MASt3R-SLAM). If someone wants dense live reconstruction in a commercial AR product,
that tension is the first thing to surface, not the last.

---

## License traps

Every entry in this lane whose license needs care, and the specific catch. Absence from this
table means the license is plain permissive with no split between code and weights.

| Repo | Stated license | The catch |
|---|---|---|
| [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | Custom Meta license, GitHub shows NOASSERTION | Not an OSI license. The original VGGT-1B checkpoint is research/non-commercial. A human must read the license text; no scanner will classify it for you |
| [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) | Apache-2.0 code | Default released weights are **CC-BY-NC 4.0**. A commercially usable variant is referenced but must be confirmed on the specific model card you download |
| [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | Apache-2.0 | Applies to the code and to Small/Base/Large weights only. The largest/Giant checkpoints are flagged as not Apache — read that model card before shipping |
| [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) | GPL-3.0 | Strong copyleft. Fine to use and modify internally; linking it into a proprietary product forces source disclosure |
| [rpng/open_vins](https://github.com/rpng/open_vins) | GPL-3.0 | Same. This is the single most common trap in AR work, because OpenVINS is otherwise the obvious VIO answer |
| [rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | CC BY-NC-SA 4.0 | **Non-commercial**, verified by reading `LICENSE.md`. Share-alike as well. No commercial use, full stop |
| [NVIDIA/cosmos](https://github.com/NVIDIA/cosmos) | OpenMDW-1.1, code and weights | An open model/data license, not a standard OSI permissive license. Do not treat it as Apache-equivalent in a compliance review |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | Apache-2.0 code | Ships a separate `LICENSE_GEMMA.txt`. PaliGemma/Gemma-derived checkpoints carry Google's model terms, which the repo badge does not reflect |
| [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | Apache-2.0 repo | Built on the LLaVA/Vicuna stack, so released checkpoints inherit Llama community license terms — including its usage restrictions |
| [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | MIT repo | Skywork weight releases do not always match the repo license. Check the Hugging Face model card before assuming MIT weights |
| [remyxai/VQASynth](https://github.com/remyxai/VQASynth) | Apache-2.0 | The pipeline is permissive; the datasets it generates inherit terms from your source images and from the depth/segmentation models used to lift them |
| [vision-x-nyu/thinking-in-space](https://github.com/vision-x-nyu/thinking-in-space) | Apache-2.0 code | The VSI-Bench videos come from ScanNet, ScanNet++ and ARKitScenes, each with its own dataset agreement and redistribution terms |
| [EvolvingLMMs-Lab/lmms-eval](https://github.com/EvolvingLMMs-Lab/lmms-eval) | Dual MIT / Apache-2.0 | MIT for the core pipeline inherited from lm-evaluation-harness, Apache-2.0 for task and model implementations. Attribute correctly if you vendor parts of it |
| [allenai/molmoact](https://github.com/allenai/molmoact) | Apache-2.0 code and weights | No trap in the license itself. The README frames it as research/educational, which is guidance, not a restriction — do not report it as a restriction, and do not report the guidance as absent |
| [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | Apache-2.0 | Some voxblox-derived files are BSD-3-Clause. Both are permissive; your attribution file needs both |
| [colmap/colmap](https://github.com/colmap/colmap) | BSD-3-Clause | GitHub reports NOASSERTION because of bundled third-party components. The project license is BSD-3; the bundled components are what need review |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | MIT | Same pattern — NOASSERTION is an artifact of bundled third-party license files, not of an unclear project license |
| [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | BSD-2-Clause | Two license files: `LICENSE.fork` for this project and `LICENSE.original` for inherited OpenVSLAM code. Ship both |
| [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | Apache-2.0 | No trap here, but the adjacent `graphdeco-inria/gaussian-splatting` is research/non-commercial and is frequently confused with it. Confirm which rasteriser a downstream project actually links |

Procedure, not opinion: for any weights-bearing entry, read the Hugging Face model card *and* the
repository LICENSE, and report them as two separate facts. `NOASSERTION` on the GitHub API means a
human has to read the file, not that the license is bad. That check is stage A of
[SECURITY-SCANNING.md](SECURITY-SCANNING.md).

---

## Limitations — what this lane will not do for you

- **No measured performance.** This catalog carries no frame rates, no VRAM figures, no accuracy
  numbers. "Real-time" here reflects what a project claims about itself. The resolution, GPU and
  view count behind that claim are unstated, so it does not transfer to a laptop GPU by default.
- **No license advice.** The flags above are research notes on what a license says. They are not
  a legal opinion, and a non-commercial flag on weights is a question for a human, not something
  an agent resolves by picking a different checkpoint URL.
- **Licenses change per artifact and per release.** A model family can relicense a checkpoint
  between versions while the repo license stays the same. Re-check on every version bump, as with
  [SECURITY-SCANNING.md](SECURITY-SCANNING.md) re-audit policy.
- **No end-to-end pipeline is provided.** Capture, reconstruction, representation and rendering
  are separate tools here. Chaining COLMAP into a splat trainer into a viewer is design work,
  not an install step.
- **Nothing here is a substitute for a calibration and metric-scale plan.** Most methods listed
  are scale-ambiguous. If the deliverable is a measurement, that constraint eliminates options
  before quality does.
- **Datasets are not covered.** ScanNet, ScanNet++, ARKitScenes and similar corpora have their
  own access agreements. This lane catalogs code and models only.
- **Nothing here has been vetted for on-device or embedded deployment.** ROS 2, CUDA and desktop
  Linux assumptions run through most of the mapping entries.

Anything not listed above goes through [skills/dep-audit](../skills/dep-audit/SKILL.md) and the
[VETTING-REPORT.md](VETTING-REPORT.md) process before it is recommended, not after.
