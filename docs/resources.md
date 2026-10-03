# Research and adoption ledger

Status: foundation documentation, 2026-10-04. This is a small decision ledger,
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
