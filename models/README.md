# Model conventions

No detector weights or tracker implementation have been selected for this
package. The earlier workstation YOLO experiment is a separate historical
baseline, not a model release or permission to redistribute its assets.

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

The [run manifest template](../docs/templates/run-manifest.v1.json) records model
identity/checksum when future runs exist. No inference feature is implemented by
this document.
