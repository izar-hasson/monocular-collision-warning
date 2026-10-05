# Third-party license audit notes

Inventory date: 2026-10-04; visibility update: 2026-10-05. The foundation has no
runtime dependencies, selected model weights, or dataset/media assets. The exact
locked developer packages and separately pinned tools have been inventoried.
The owner made the repository public. A project source license remains unselected;
public visibility does not select a license.

## Foundation tool inventory

Checked version-specific PyPI metadata for every non-project entry in `uv.lock`,
setuptools 84.0.0, and uv 0.12.23. Inspected available installed license/notice
files and recorded their hashes in
[third-party-license-inventory.json](third-party-license-inventory.json).
The table records declared top-level licenses, not a complete vendored-component
redistribution audit. Colorama is Windows-only and was not installed in the
Ubuntu environment; its exact-version upstream page identifies BSD-3-Clause.

| Component / exact version metadata | Declared license | Use |
| --- | --- | --- |
| [ast-serialize 0.12.1](https://pypi.org/project/ast-serialize/0.12.1/) | MIT | locked developer dependency |
| [cfgv 3.5.0](https://pypi.org/project/cfgv/3.5.0/) | MIT | locked developer dependency |
| [colorama 0.4.6](https://pypi.org/project/colorama/0.4.6/) | BSD-3-Clause | locked developer dependency |
| [distlib 0.4.3](https://pypi.org/project/distlib/0.4.3/) | PSF-2.0 | locked developer dependency |
| [filelock 4.0.9](https://pypi.org/project/filelock/4.0.9/) | MIT | locked developer dependency |
| [identify 2.6.20](https://pypi.org/project/identify/2.6.20/) | MIT | locked developer dependency |
| [iniconfig 2.3.0](https://pypi.org/project/iniconfig/2.3.0/) | MIT | locked developer dependency |
| [librt 0.16.0](https://pypi.org/project/librt/0.16.0/) | MIT | locked developer dependency |
| [mypy 2.4.0](https://pypi.org/project/mypy/2.4.0/) | MIT | locked developer dependency |
| [mypy-extensions 1.1.0](https://pypi.org/project/mypy-extensions/1.1.0/) | MIT | locked developer dependency |
| [nodeenv 1.11.0](https://pypi.org/project/nodeenv/1.11.0/) | BSD-3-Clause | locked developer dependency |
| [packaging 26.3](https://pypi.org/project/packaging/26.3/) | Apache-2.0 OR BSD-2-Clause | locked developer dependency |
| [pathspec 1.1.1](https://pypi.org/project/pathspec/1.1.1/) | MPL-2.0 | locked developer dependency |
| [platformdirs 4.12.2](https://pypi.org/project/platformdirs/4.12.2/) | MIT | locked developer dependency |
| [pluggy 1.6.0](https://pypi.org/project/pluggy/1.6.0/) | MIT | locked developer dependency |
| [pre-commit 4.6.2](https://pypi.org/project/pre-commit/4.6.2/) | MIT | locked developer dependency |
| [pygments 2.21.0](https://pypi.org/project/pygments/2.21.0/) | BSD-2-Clause | locked developer dependency |
| [pytest 9.1.1](https://pypi.org/project/pytest/9.1.1/) | MIT | locked developer dependency |
| [python-discovery 1.6.1](https://pypi.org/project/python-discovery/1.6.1/) | MIT | locked developer dependency |
| [pyyaml 6.0.3](https://pypi.org/project/pyyaml/6.0.3/) | MIT | locked developer dependency |
| [ruff 0.16.10](https://pypi.org/project/ruff/0.16.10/) | MIT | locked developer dependency |
| [typing-extensions 4.16.0](https://pypi.org/project/typing-extensions/4.16.0/) | PSF-2.0 | locked developer dependency |
| [virtualenv 21.14.5](https://pypi.org/project/virtualenv/21.14.5/) | MIT | locked developer dependency |
| [setuptools 84.0.0](https://pypi.org/project/setuptools/84.0.0/) | MIT | isolated build backend |
| [uv 0.12.23](https://pypi.org/project/uv/0.12.23/) | MIT OR Apache-2.0 | tool outside project lock |

Relevant bundled notices found during review:

- mypy includes Apache-2.0 typeshed license text in addition to its own MIT license.
- ast-serialize includes a separate MIT notice for bundled Ruff crates.
- virtualenv includes `THIRD-PARTY-NOTICES.md` for embedded wheels and their
  own licenses. Review the exact notices if redistributing the tool environment.
- pathspec declares MPL-2.0; retain its exact license and review obligations
  if modifying or redistributing that package. It is a developer dependency,
  not part of this project’s runtime wheel.

Upstream tool terms remain separate from the project source license. Retain
applicable license/notices with any redistributed third-party code, binaries
or environment. Do not infer permission for associated weights/data from a
library declaration. This inventory is engineering evidence; public release
requires a review of the actual release contents and any vendored notices.

## Future integrations

| Category | Candidate | Gate before adoption or redistribution |
| --- | --- | --- |
| Library | Ultralytics, PyTorch, OpenCV, tracker implementation | Select exact versions, read primary license files and transitive notices, document intended use and unresolved questions |
| Model | Detector pretrained weights | Record exact source/version/SHA-256 and separate weight terms; review acquisition/use/redistribution |
| Dataset/media | Dashcam clips, labels, screenshots, calibration | Record source/access rights, license/terms, attribution, sequence splits and privacy/redaction decision |
| Repository | Original project source | Owner selects a public license after integration/release review; no unverified LICENSE boilerplate |

The [Ultralytics licensing page](https://www.ultralytics.com/license) describes
AGPL-3.0 and Enterprise options for its code/models. Record the exact proposed
library/weight terms and intended use before integrating it; do not treat the
earlier separate workstation demo as this package’s license clearance.
No Ultralytics package or weights were added during foundation setup.

Data/model conventions are in [data/README.md](../data/README.md) and
[models/README.md](../models/README.md). Unclear rights/provenance leave a
candidate deferred. The [resource ledger](resources.md) records discovery
separately from adoption.
