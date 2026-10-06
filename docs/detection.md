# Testing detection

The runnable test script is a thin checkout entry point to the same runner and
pipeline as `collision-warning detect`. It uses the existing YOLO environment
and saves annotated frames. Video input uses the shared PyAV reader.
Install PyAV in that environment once:

```bash
../collision-warning/.venv/bin/python -m pip install --only-binary=:all: --no-deps av==19.0.1
```

The repository's optional video dependencies are locked separately:
`uv sync --locked --extra video`. This installs PyAV/NumPy for decoding and
generated-video tests; detector dependencies still come from the YOLO environment.

From the project root, test the acquired KITTI sample:

```bash
../collision-warning/.venv/bin/python scripts/test_detection.py \
  --source data/external/kitti-0005 \
  --weights ../collision-warning/yolo11n.pt \
  --device cuda:0
```

For the existing bus image, use `--source ../collision-warning/bus.jpg`. For your
own video, use `--source /path/to/video.mp4`. Use `--device cpu` to test without
GPU access. `--conf 0.25`, `--imgsz 640`, `--max-frames 100` and COCO road-user
classes are the defaults; `--help` lists the available controls. `--warmup-frames`
defaults to 5: those frames are still detected and logged, but excluded from
warmed timing summaries, matching the full CLI.

Each run creates a new `outputs/detection-test-<id>/` with annotated JPEG frames,
`detections.jsonl` (boxes, names, scores and source times), and `manifest.json`
(weights checksum, versions, configuration and counts). `--output` selects a
specific new directory; existing results are preserved. Counts are detection
observations across frames, not unique tracked objects. `--expected-sha256`
optionally verifies an independently obtained weight hash; otherwise the actual
local hash is recorded without claiming upstream authenticity.

The script loads this checkout's `src` and calls `cli.detection_test_main`.
Shared argument parsing calls `run.detect_source`, which loads the input and
detector, then calls `pipeline.run_detection` once. `inputs.py` handles images
and KITTI; `video.py` handles video; `preview.py` optionally renders the same
detections. Running it does not install dependencies; source-checkout testing
remains separate from installed-package validation.

Both entry points now write the same JSONL and run-manifest schema. The manifest
stores counts and timing under `metrics`, configuration under `configuration`,
and versions under `environment.package_versions`. JSONL includes BGR color-space
and warm-up markers; preview runs also record annotated image names. Preview
rendering is included in the pipeline's output timing and identified in the
manifest. The script accepts optional `--clip-manifest` and `--model-manifest`;
without them, it records local hashes and marks provenance as not supplied.
The full CLI continues to require both input manifests.

KITTI directories must contain numbered PNGs and `timestamps.txt`. Their source
timestamp differences retain nanosecond precision. Still images have no temporal
measurement. Video input preserves `pts * time_base`, including nonzero origins
and irregular intervals, and rejects missing or non-increasing timestamps.
OpenCV draws annotations and writes preview videos. `--save-video` uses the
stream's nominal FPS for playback; JSONL retains the original presentation times.

Verified on 2026-10-06 with the existing environment on CPU: the bus image
produced one bus and four people; all 12 KITTI frames produced observations and
annotated images. This is smoke evidence, not a detection-accuracy evaluation.

After PyAV installation, the same 12 KITTI frames were encoded losslessly into
`data/external/kitti-0005-pyav-smoke.mkv` for a video smoke run. Its local JSON card
records a 5-second timestamp origin and millisecond rounding. The script decoded
all 12 frames through `video.read_video`, preserving the encoded timestamps
(5.000–6.136 seconds), and produced 79 detections plus 12 annotated JPEGs and a
decodable MP4 under `outputs/pyav-video-detection-smoke/`. Reproduce this locally:

```bash
../collision-warning/.venv/bin/python scripts/test_detection.py \
  --source data/external/kitti-0005-pyav-smoke.mkv \
  --weights ../collision-warning/yolo11n.pt \
  --device cpu --max-frames 12 --save-video
```

This exercises real video decoding and inference on a generated input. The full
CLI's recorded-video acceptance and locked GPU migration remain separate gates.

After consolidating the runner, CPU verification repeated the bus, KITTI and
video runs with the same counts. Current artifacts are under
`outputs/shared-pipeline-image-smoke/`, `outputs/shared-pipeline-kitti-smoke/` and
`outputs/shared-pipeline-video-smoke/`. All three use the shared output schema;
the video run preserves PTS and includes a verified 12-frame annotated MP4.

## Full Phase 1 CLI

Phase 1 implementation, authorized 2026-10-05. The
[detection/tracking plan](detection-tracking-plan.md) defines the acceptance gates.
Default CPU checks use synthetic inputs; real detector evidence is separate.

## Inputs

Use a local timestamped video and local YOLO detection weights. Each input needs
a version-1 JSON manifest. The compact run-input records supplement the detailed
[clip card](templates/clip-manifest.v1.json), rather than replacing dataset review.

Clip example (replace every placeholder with reviewed evidence):

```json
{
  "schema_version": 1,
  "id": "dataset-sequence-camera-segment",
  "sha256": "actual SHA-256 of the local video",
  "source_url": "exact upstream source",
  "license": "exact terms/version and URL",
  "permitted_use": "documented basis for this research use",
  "split": "development"
}
```

Model example:

```json
{
  "schema_version": 1,
  "id": "yolo11n",
  "sha256": "actual SHA-256 of the local weights",
  "source_url": "verified upstream acquisition URL or process",
  "license": "reviewed library and weight terms",
  "permitted_use": "documented basis for local experimentation"
}
```

Keep completed manifests, weights, raw clips and derived artifacts under ignored
`data/`, `models/` and `runs/`. Never put a private machine path in a tracked
manifest. Hash checks validate identity, not the correctness of rights statements.
No input acquisition occurs in the command.

## Command

The `gpu` extra pins the working Linux x86_64 / Python 3.12 inference baseline:
PyTorch 2.14.1+cu130, torchvision 0.29.1+cu130, Ultralytics 8.4.172,
OpenCV 5.0.0.93, PyAV 19.0.1 and NumPy 2.5.2. Torch and torchvision use the
explicit official cu130 index. Transitive baseline constraints prevent unrelated
CUDA support, Polars and inference dependency migrations. The shared lock now
selects filelock 3.32.3 (previous CPU lock: 4.0.9) and NumPy 2.5.2 (previous video
lock: 2.5.3). Other existing developer versions are preserved.

Keep the sibling environment intact. Create the separate project GPU environment:

```bash
UV_PROJECT_ENVIRONMENT=.venv-gpu uv sync --locked --extra gpu --no-dev
.venv-gpu/bin/collision-warning --help
```

The default `uv sync --locked` remains a CPU developer installation without CUDA
or model packages. Once the GPU environment exists, invoke its executable
explicitly; a default `uv run` would select the CPU environment instead.

After installing and verifying the optional inference environment, run:

```bash
collision-warning detect \
  --source data/raw/driving.mkv \
  --weights models/yolo11n.pt \
  --clip-manifest data/raw/driving.manifest.json \
  --model-manifest models/yolo11n.manifest.json \
  --output runs/detection-demo \
  --device cuda:0 --imgsz 640 --conf 0.1 \
  --classes 0 1 2 3 5 7 --warmup-frames 5 --max-frames 30
```

`cpu` is the explicit default device. `--imgsz` sets a square letterbox inference
shape; output boxes refer to source pixels. The listed classes assume the COCO
mapping. Every processed frame, including empty scenes and warm-up frames, is
written to `detections.jsonl`. The source PTS origin and intervals are preserved.
Missing/duplicate/backward timestamps fail the run. A frame limit stops decoding
without consuming one extra frame. Existing run directories are preserved.

## Outputs and timing

`manifest.json` includes input/model identity and rights, configuration, installed
versions, checkout/lock identity when available, device and stage metrics. Failed
runs retain a failure record and any partial observations; do not score them as
complete runs. A wheel outside a checkout may not have code/lock identity; retain
the wheel checksum separately when reproducing those runs.

Decode, detection, JSONL output and total timings use processing wall time.
Inference timing synchronizes CUDA. Model loading and first frame are separate;
the first five frames are retained but excluded from warmed percentiles by
default. A shorter video has unavailable warmed metrics rather than zeros.
Source observed rate is `(N-1)/(last PTS-first PTS)` over processed frames; it is
not container nominal FPS. Repeated runs on fixed clips/config/device are needed
for useful performance conclusions. No reference-box accuracy, TTC/range,
collision probability or warning performance is inferred from a successful demo.


## KITTI acceptance reproduction

Use the first 100 consecutive `image_02` frames of raw sequence
`2011_09_26_drive_0005`. All excerpts of this sequence belong to development;
reserve other sequences for held-out evaluation. The acquisition script verifies
ZIP CRCs and records each source PNG SHA-256 and the complete timestamp-file hash.
Media stays ignored and local under KITTI's CC-BY-NC-SA-3.0 terms.

```bash
python scripts/acquire_kitti_sample.py --destination data/external/kitti-0005 --frames 100
.venv-gpu/bin/python scripts/prepare_detection_clip.py \
  --source data/external/kitti-0005 \
  --output data/external/kitti-0005-acceptance.mkv --frames 100
.venv-gpu/bin/python scripts/verify_detection_acceptance.py \
  --source data/external/kitti-0005-acceptance.mkv \
  --weights models/yolo11n.pt \
  --clip-manifest data/external/kitti-0005-acceptance.json \
  --model-manifest models/yolo11n.json \
  --output outputs/phase1-acceptance
```

The encoder writes the completed clip card beside the video, containing original
source timestamp strings, development split, dimensions, hashes, codec settings,
expected PTS, encoding library versions and limitations. It verifies exact pixel
equality and PTS for every decoded frame. Relative KITTI times are shifted by
five seconds and rounded to milliseconds; maximum rounding error is recorded.
Nominal 10 FPS metadata does not replace the source intervals. This is video
encoded from a recorded image sequence, not a native camera video file.

Weights and `models/yolo11n.json` are local inputs reviewed before running;
the verifier never acquires a model. The baseline SHA-256 is
`0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
The model card records the Ultralytics asset URL, model/task/COCO mapping,
AGPL/Enterprise terms, local acquisition process and its provenance limitations.
A local identity hash does not independently prove upstream authenticity.

The acceptance runner calls the installed full CLI three times using CUDA:0,
FP32, batch one, square 640 letterboxing, confidence 0.1, COCO classes
0/1/2/3/5/7, 10 warm-up frames, all 100 frames, JPEG and MP4 previews. It validates
all JSONL timestamps/indices, source bounds/scores, warm-up flags, counts, JPEGs,
and decoded preview frame counts/dimensions. Each repetition reports detection
and total mean/p50/p95, warmed and overall processed FPS, and observed source FPS.
It also checks existing-output protection, mismatched weights, missing input,
invalid CUDA devices and corrupt video. Synthetic CPU tests additionally cover
missing/duplicate/backward timestamps, empty scenes and partial-output failures.

All results are local under `outputs/phase1-acceptance/`; repeated invocations
require a new output directory. Preview MP4 uses nominal 10 FPS and pads the odd
375-pixel height to 376; JSONL retains the original 1242×375 coordinate system and
source PTS. Frame latency includes drawing, JPEG/MP4 writes and JSONL flushing,
but excludes model loading, provenance hashing, preview finalization and final
manifest writing. Visual review and hosted CPU CI remain explicit closure gates.
