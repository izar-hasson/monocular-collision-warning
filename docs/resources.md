# Research and adoption ledger

Status: updated for local detection trials, 2026-10-06. This is a small decision ledger,
not an integration backlog. Entries below come from [HANDOFF.md section 8](../HANDOFF.md#8-research-library--explicit-adoption-decisions).
The companion `Useful-tools-updated.md` is not present in this checkout; its full
contents have not been independently audited here.

The three discovery directories are [API Vault](https://apivault.dev/) /
[catalog](https://github.com/exa-studio/ApiVault),
[Applied ML](https://github.com/eugeneyan/applied-ml), and
[Build Your Own X](https://github.com/codecrafters-io/build-your-own-x).
These are references, not installed dependencies. A directory entry establishes
neither suitability nor permission to use associated assets.

| Candidate / direct source | Discovery and intended use | Priority / decision |
| --- | --- | --- |
| [Roboflow Universe](https://universe.roboflow.com/) | API Vault; possible discovery of future footage/annotations. Exact dataset, sequence quality, license, calibration and reference labels have not been checked | NEXT / deferred; no dataset selected or acquired |
| [Google Rules of ML](https://developers.google.com/machine-learning/guides/rules-of-ml) | Applied ML / handoff; baseline and experiment-traceability guidance already informs the foundation | NOW / adopted as engineering guidance in the handoff; not a runtime dependency or validation result |
| Build Your Own X collections | Optional learning examples only when a concrete need appears | LEARNING / deferred; no tutorial or code selected |
| [KITTI raw](https://www.cvlibs.net/datasets/kitti/raw_data.php) / [official AWS mirror](https://registry.opendata.aws/kitti/) | Independent research; original RGB sequences and timestamps for local detection/continuity examples. Terms: CC-BY-NC-SA-3.0, attribution and noncommercial restrictions | NOW / adopted for acceptance: 100 verified consecutive development frames from `2011_09_26_drive_0005`, camera `image_02`. Acquisition/checksums/terms are local in `data/external/kitti-0005/acquisition.json`. No media published or reference labels acquired |
| [Ultralytics YOLO](https://docs.ultralytics.com/modes/predict/) / [terms](https://www.ultralytics.com/license) | Existing local YOLO11n weights and Ultralytics 8.4.172; local visual detector smoke. Library/model AGPL/enterprise terms remain separate from source license selection | NOW / tried locally with recorded checksum and CPU output; no public release or source license selected |

Before trying or adopting a specific item, replace catalog evidence with direct
upstream documentation and complete this record:

```text
Name and exact official/upstream URL:
Type: dataset | model | library | API | paper/case study | tutorial | benchmark
Discovered via: API Vault | Applied ML | Build Your Own X | independent research
Documented capability (fact, primary source):
Intended pipeline use, phase and measurable need (our proposal):
Access/license/region/provenance/privacy/maintenance: checked date + evidence
Alternatives and reason to prefer or defer:
Priority: NOW | NEXT | OPTIONAL | LEARNING
Decision: candidate | tried | adopted | rejected | deferred; rationale / ADR
Reproduction: version, exact URL/hash, commands and experiment ID if tried
```

Keep an item deferred when rights, evidence or need are unclear. Temporal risk
logic must remain inspectable in this package; discovery services do not replace
monocular measurement contracts or authorize hosted image inference. Mapping,
weather, telemetry and cloud integrations remain deferred. Data/model terms and
redistribution decisions belong in the [license ledger](third-party-licenses.md).
