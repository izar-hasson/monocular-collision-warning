# Data conventions

No dataset, clip, annotation, or calibration has been acquired for this package.
The files here document future acquisition; they are not evidence of evaluation.

Keep media outside Git. When the corresponding stages exist, use local
`data/external/` for acquired assets, `data/raw/` for immutable original inputs,
`data/interim/` for reproducible intermediate products, and `data/processed/` for
reviewed evaluation inputs. Create a stage only when it has a real consumer.
These directories and their contents are ignored; only this README is tracked.

Before using a clip, complete a record based on
[clip-manifest.v1.json](../docs/templates/clip-manifest.v1.json):

| Field | Required evidence |
| --- | --- |
| Identity | Dataset/version, clip and source sequence IDs, exact upstream URL, acquisition date, local relative path, original SHA-256 |
| Rights | Exact license/terms URL and version, access basis, allowed research use, redistribution decision, attribution and restrictions |
| Sequence split | Development or held-out evaluation; group by source sequence/journey and record duplicate/overlap checks |
| Video | Container, dimensions, color space, duration and source presentation-time convention; document missing/nonuniform timestamps |
| Reference labels | Label types, units, coordinate frames, source, annotation version, quality/uncertainty and alignment with video |
| Calibration | Intrinsics, height/pitch, distortion and calibration source/checksum when present; otherwise explicitly unavailable |
| Privacy | Faces, plates and location exposure; review/redaction decision and derived-file checksum |

Use SHA-256 on the actual local file (`sha256sum /path/to/clip` on Ubuntu).
Preserve the original privately; record any authorized redaction/transcoding as a
new derived asset with its own checksum and recipe. A source URL alone is not a
license or proof of permission to redistribute a clip or screenshot.

Split by sequence before extracting frames. Keep related segments and duplicate
uploads in one split. Freeze held-out IDs before model/threshold tuning; record
any later changes. Bounding-box labels alone do not establish metric distance,
reference TTC, or collision-warning events. External reference sensors are for
evaluation; inference remains monocular RGB.

See [evaluation-plan.md](../docs/evaluation-plan.md) and the
[license ledger](../docs/third-party-licenses.md). Rights/reference uncertainty
leaves a candidate deferred. No download is part of package import or CPU tests.
