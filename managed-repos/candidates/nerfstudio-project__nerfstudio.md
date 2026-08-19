# Managed adoption candidate: nerfstudio-project/nerfstudio

Status: **OWNER REVIEW REQUIRED**

`nerfstudio-project/nerfstudio` remains a major Apache-2.0 NeRF toolkit, but its repository has crossed the Master Repo active-runtime removal threshold because the last upstream push is more than one year old. The active 3D lane already contains newer maintained tooling such as `MrNeRF/LichtFeld-Studio` and `nerfstudio-project/gsplat`.

## Potentially useful pieces

- Dataset/data-parser abstractions.
- Training/evaluation CLI patterns.
- Camera, rendering, export, viewer, and plugin architecture.
- NeRF-specific workflows not covered by Gaussian-splatting-first replacements.

## Adoption plan

1. Deep-scan the final upstream revision and dependency graph.
2. Preserve Apache-2.0 license/notice requirements.
3. Identify features not already covered better by current active catalog repos.
4. Prefer extracting small compatibility adapters over maintaining the entire historical stack.
5. Update Python/PyTorch/CUDA/viser/gsplat/colmap-related dependencies and platform setup.
6. Add modern CI, dependency scanning, reproducible environment files, smoke tests, and GPU-optional test paths.
7. Create a Charles-managed repository only if the unique value justifies the maintenance cost and Charles approves the scope.
8. Re-run all Master Repo security and freshness gates before adding the maintained replacement back to the active catalog.
