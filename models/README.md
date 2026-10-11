# Model conventions

Phase 1 uses local YOLO11n COCO detection weights with Ultralytics 8.4.172. Their
SHA-256 is `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`;
`models/yolo11n.json` records acquisition, library/model terms, class mapping and
permitted local experimentation. The initial weights were copied from the
owner's preserved baseline. On 2026-10-11, an independent re-download from the
recorded official Ultralytics asset URL matched that SHA-256 exactly.
Weights remain ignored, and no model release or media redistribution is part of
Phase 1. No tracker has been selected or implemented yet. See the
[acceptance evidence](../docs/evidence/phase1-detection.json).

Store approved weights locally under `models/` or an external asset directory;
weights are ignored by Git. Before adoption, record:

- Model ID, architecture, upstream release/commit and associated library version.
- Exact file URL or approved acquisition procedure, access date, original file
  name, local relative path, byte size and SHA-256 of the downloaded file.
- Library/code license and separate weight license/terms, required attribution,
  permitted uses, redistribution decision and unresolved questions.
- Model input/color/normalization and class mapping, intended use and limitations.
- Reviewed CPU/CUDA package versions, device/precision and measured smoke evidence.

Verify the expected checksum before use; retain acquisition and terms evidence
alongside a local manifest. A model alias or package version is not a weight
checksum. Do not add weights to commits, download on import, or make default CPU
tests depend on model/network access. Future adapters must permit fake-detector
contract tests and explicit local asset selection.

[Ultralytics review](../docs/third-party-licenses.md#future-integrations) must be
completed for the exact proposed library and weights before adoption. Do not
infer that a project source license covers upstream weights. Preserve the
[known GPU environment](../docs/environment-baseline.md) until an optional CUDA
installation has been separately verified.

The full CLI requires a completed local model card, verifies the weight hash
before loading, and includes that identity and installed versions in each run
manifest. The [run manifest template](../docs/templates/run-manifest.v1.json)
describes additional evidence for later evaluation stages.
