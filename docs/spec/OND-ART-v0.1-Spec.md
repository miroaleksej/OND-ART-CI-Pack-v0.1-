# OND-ART v0.1 Specification (Draft)

**OND-ART (Observed Nonce/Randomness Dynamics — Algorithmic Regularity Test)** is a protocol-level audit of randomness usage through the observable dynamics of public artifacts (e.g., digital signatures).

OND-ART:
- analyzes **post-protocol dynamics**, not raw RNG bits;
- produces a **structural profile + confidence intervals**, not a binary “pass/fail”;
- is not intended for key recovery / nonce recovery and makes no security claims.

## Related research (non-normative)

- `../methodology/README.md`

## Normative requirements (summary)

### Observation map π
`π` SHALL be:
- deterministic and publicly documented (`pi_id`, `pi_version`, `pi_spec_hash`);
- dependent only on public data;
- emitting observations of fixed structure (fixed dimension/type).

#### Observation space (obs_space)
- if `type = R^d`, then `d` is required
- if `type = Z_mod_m`, then `modulus` is required

### Sampling
- Core: `N >= 10_000`
- Recommended: `N >= 100_000`
- Bootstrap: `B >= 200` (core), `B >= 1000` (recommended)

### Metrics
OND-ART v0.1 uses three orthogonal metrics:
- `rank` (Rank-Entropy)
- `subspace` (Subspace Occupancy)
- `branching` (Branching Index)

### Reporting
- human-readable report (optional)
- machine-readable JSON report (required): structure is defined by `schemas/ond-art-report-0.1.schema.json`
- standard disclaimer in `notes`: `Diagnostic only; no security claim.` (recommended)

#### Scheme-specific params (examples in schema)
- for `context.scheme = ECDSA-P256`, `context.params.hash` is required

### Baseline/Regression
Baseline comparison MAY be `null` (if not performed) or an object:
- `distance`, `distance_ci95`
- `thresholds` (`green`, `yellow`, `red`)
- `classification` ∈ {Within Baseline Envelope, Deviating, Strong Deviation}

---

The full specification text can live in the main OND repository as a separate document. This file is a short “engineering” version for CI/QA.
