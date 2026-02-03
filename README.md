# OND-ART CI Pack (v0.1)

Minimal, ready-to-use package for **validating OND-ART machine reports in CI**:

- ✅ JSON Schema (Draft 2020-12) for OND-ART v0.1 reports  
- ✅ GitHub Actions workflow for PR/push validation  
- ✅ Python validator: **schema + additional invariants** (CI order, threshold monotonicity, etc.)  
- ✅ Example reports

> Important: OND-ART is a diagnostic structural audit. It **does not** make security claims and does not replace SP 800-22 / SP 800-90.

## Structure

```
.github/workflows/ond-art-validate.yml
schemas/ond-art-report-0.1.schema.json
scripts/validate_ond_art_reports.py
ond_art_ci_pack/
examples/*.json
tests/
docs/spec/OND-ART-v0.1-Spec.md
docs/methodology/README.md
docs/methodology/research/*.md
pyproject.toml
LICENSE
```

## Quick start (local)

```bash
python -m pip install jsonschema
export SCHEMA_PATH=schemas/ond-art-report-0.1.schema.json
export REPORT_GLOB=examples/*.json
python scripts/validate_ond_art_reports.py
```

## Install (pip) and CLI

```bash
python -m pip install -e .
ond-art-validate
```

The CLI uses the same environment variables (`SCHEMA_PATH`, `REPORT_GLOB`, etc.).

## Tests

```bash
python -m pip install -e .[test]
python -m pytest
```

## Usage in your repo

1) Copy `schemas/`, `scripts/`, and `.github/workflows/` into your repo.  
2) Store reports under `reports/**.json` (or change `REPORT_GLOB` / `paths` in the workflow).  
3) (Optional) Control the failure policy by baseline.classification:
   - by default the workflow fails on `Strong Deviation`
   - you can extend the list or disable it (empty string)

## Conformance profiles (spec.profile)

The schema can **gate minimum thresholds** based on `spec.profile`:

- `core` (or if profile is missing): `N >= 10_000`, `B >= 200`
- `recommended`: `N >= 100_000`, `B >= 1000`
- `dev`: only base minimums (`N >= 2`, `B >= 1`)

The workflow can also **inject a default profile** (DEFAULT_PROFILE) if the producer omits it.

## Diagnostic-only policy

OND-ART is a diagnostic structural audit. It **does not make security claims** and does not replace SP 800-22 / SP 800-90.  
It is recommended to include the standard disclaimer in `notes`:  
`Diagnostic only; no security claim.`

## Spec/CI vs Research/Methodology

- **Spec/CI**: formal report structure + CI validation.  
  Primary document: `docs/spec/OND-ART-v0.1-Spec.md`.
- **Research/Methodology**: theoretical work and research, **non-normative**, and  
  **not a replacement for SP 800-22/90** or other RNG testing standards.

## Research notes (reference only)

These materials are **not normative** and do not change the diagnostic-only policy.

### `docs/methodology/research/new-horizons.md`

Explores theoretical extensions of OND as an ontology of observation.  
Reframes signatures as measurements in a phase space rather than static objects.  
Introduces the idea of RNG dynamics as trajectories through observable state.  
Sketches links to ergodicity, mixing, and return-time analysis in discrete settings.  
Outlines an “observability theory” view of hidden automata behind signatures.  
Positions these as conceptual horizons, not validation requirements.  
Does **not** define tests or claims, and does **not** replace SP 800-22/90.  
Use it as a research compass, not as CI criteria.

### `docs/methodology/research/inverse-task.md`

Discusses the inverse problem: recovering hidden structure from observable traces.  
Frames when the observation map might allow (or block) reconstruction.  
Highlights identifiability limits and what is fundamentally unobservable.  
Connects the inverse task to stability, noise sensitivity, and model mismatch.  
Suggests how inverse reasoning could guide experimental design.  
Explicitly separates theory from diagnostics and implementation.  
Does **not** constitute security claims or RNG validation.  
Treat as research background for future methodology refinement.

## Additional invariants (beyond Schema)

`validate_ond_art_reports.py` additionally checks:

- `ci95` is `[low, high]` and `low <= high`
- metric value lies within its `ci95` (with a tiny tolerance)
- `baseline.thresholds` satisfy `green <= yellow <= red`
- `baseline.distance` lies within `baseline.distance_ci95`
- `data.invalid_count <= data.N`
- forbidden `baseline.classification` (FORBID_CLASSIFICATION)
- optional: `baseline.classification` vs thresholds consistency (STRICT_CLASSIFICATION=1)
- optional: required diagnostic disclaimer in `notes` (REQUIRE_DISCLAIMER=1)

## Environment options (script)

- `SCHEMA_PATH`: schema path (default `schemas/ond-art-report-0.1.schema.json`)
- `REPORT_GLOB`: report glob (default `reports/**/*.json`)
- `FORBID_CLASSIFICATION`: forbidden classifications (default `Strong Deviation`)
- `DEFAULT_PROFILE`: injected profile if `spec.profile` is missing (default `core`)
- `STRICT_CLASSIFICATION`: if `1`, error on classification/threshold mismatch (default `0`)
- `REQUIRE_DISCLAIMER`: if `1`, require `Diagnostic only; no security claim.` in `notes` (default `0`)

## Release versioning
Package version lives in `pyproject.toml` and is mirrored in `ond_art_ci_pack/__init__.py`.  
Update both in lockstep for releases.

## Licensing

This package is distributed under the MIT License — see `LICENSE`.
#ONDART #CI #JSONSchema #GitHubActions #Python #Validation #Diagnostics #Cryptography #RNG #RandomnessAudit
ond-art, json-schema, github-actions, ci, python, validation, cryptography, rng, audit.

This package is distributed under the MIT License — see `LICENSE`.
