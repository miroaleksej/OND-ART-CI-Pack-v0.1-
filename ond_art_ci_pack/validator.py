"""Validate OND-ART reports against JSON Schema + additional invariants.

Environment variables (used by GitHub Actions workflow):
- SCHEMA_PATH: path to schema JSON (default: schemas/ond-art-report-0.1.schema.json)
- REPORT_GLOB: glob for reports (default: reports/**/*.json)
- FORBID_CLASSIFICATION: comma-separated forbidden baseline.classification values (default: Strong Deviation)
- DEFAULT_PROFILE: if spec.profile is missing, inject this profile for validation (default: core)
- STRICT_CLASSIFICATION: if '1', treat classification-vs-threshold inconsistencies as errors (default: 0)
- REQUIRE_DISCLAIMER: if '1', require standard diagnostic disclaimer in notes (default: 0)
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator, FormatChecker

TOL = 1e-12
DISCLAIMER_TEXT = "Diagnostic only; no security claim."


def gh_error(file: str, message: str) -> None:
    print(f"::error file={file}::{message}")


def gh_warning(file: str, message: str) -> None:
    print(f"::warning file={file}::{message}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_summary_line(line: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as s:
        s.write(line + "\n")


def ensure_ci_order(ci: List[float], path: str) -> Optional[str]:
    if len(ci) != 2:
        return f"{path} must have length 2"
    lo, hi = ci
    if lo - hi > TOL:
        return f"{path} invalid: low ({lo}) > high ({hi})"
    return None


def num_in_interval(x: float, ci: List[float]) -> bool:
    lo, hi = ci
    return (x + TOL) >= lo and (x - TOL) <= hi


def check_required_numeric_in_ci(label: str, value: Any, ci: Any, errors: List[str]) -> None:
    if not isinstance(value, (int, float)) or not isinstance(ci, list) or len(ci) != 2:
        return
    if not num_in_interval(float(value), [float(ci[0]), float(ci[1])]):
        errors.append(f"{label} value {value} is outside ci95 {ci}")


def get_nested(obj: Dict[str, Any], keys: List[str]) -> Any:
    cur: Any = obj
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


def has_required_disclaimer(notes: Any) -> bool:
    if not isinstance(notes, list):
        return False
    for item in notes:
        if isinstance(item, str) and DISCLAIMER_TEXT.lower() in item.lower():
            return True
    return False


def inject_default_profile(report: Dict[str, Any], default_profile: str) -> None:
    spec = report.get("spec")
    if not isinstance(spec, dict):
        return
    if "profile" not in spec or not isinstance(spec.get("profile"), str) or not spec.get("profile"):
        spec["profile"] = default_profile


def main() -> int:
    schema_path = Path(os.environ.get("SCHEMA_PATH", "schemas/ond-art-report-0.1.schema.json"))
    report_glob = os.environ.get("REPORT_GLOB", "reports/**/*.json")
    forbid_raw = os.environ.get("FORBID_CLASSIFICATION", "Strong Deviation").strip()
    forbid = [x.strip() for x in forbid_raw.split(",") if x.strip()]
    default_profile = os.environ.get("DEFAULT_PROFILE", "core").strip() or "core"
    strict_classification = os.environ.get("STRICT_CLASSIFICATION", "0").strip() == "1"
    require_disclaimer = os.environ.get("REQUIRE_DISCLAIMER", "0").strip() == "1"

    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        return 1

    try:
        schema = load_json(schema_path)
    except Exception as e:
        print(f"Invalid schema JSON: {e}")
        return 1

    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    files = sorted(glob.glob(report_glob, recursive=True))
    if not files:
        print(f"No report files found for glob: {report_glob}")
        write_summary_line("⚠️ No report files found; nothing to validate.")
        return 0

    write_summary_line("# OND-ART validation")
    write_summary_line(f"- Schema: `{schema_path}`")
    write_summary_line(f"- Reports glob: `{report_glob}`")
    write_summary_line(f"- DEFAULT_PROFILE (if missing): `{default_profile}`")
    write_summary_line(f"- STRICT_CLASSIFICATION: `{'1' if strict_classification else '0'}`")
    write_summary_line(f"- REQUIRE_DISCLAIMER: `{'1' if require_disclaimer else '0'}`")
    if forbid:
        write_summary_line(f"- Forbidden baseline.classification: `{', '.join(forbid)}`")
    write_summary_line("")

    any_failed = False

    for f in files:
        p = Path(f)
        if p.name.endswith(".schema.json"):
            continue

        # Load report
        try:
            report = load_json(p)
        except Exception as e:
            gh_error(f, f"Invalid JSON: {e}")
            write_summary_line(f"## ❌ `{f}`")
            write_summary_line(f"- Invalid JSON: {e}")
            write_summary_line("")
            any_failed = True
            continue

        # Inject default profile (so CI can enforce a chosen profile even if the producer omits it)
        if isinstance(report, dict):
            inject_default_profile(report, default_profile)

        # Schema validation
        errors = sorted(validator.iter_errors(report), key=lambda e: list(e.path))
        if errors:
            print(f"::group::Schema errors in {f}")
            for err in errors:
                loc = "/" + "/".join(str(x) for x in err.path)
                gh_error(f, f"{loc}: {err.message}")
            print("::endgroup::")

            write_summary_line(f"## ❌ `{f}`")
            for err in errors[:25]:
                loc = "/" + "/".join(str(x) for x in err.path)
                write_summary_line(f"- `{loc}`: {err.message}")
            if len(errors) > 25:
                write_summary_line(f"- …and {len(errors) - 25} more")
            write_summary_line("")
            any_failed = True
            continue

        # Additional invariants
        extra_errors: List[str] = []
        extra_warnings: List[str] = []

        # invalid_count <= N
        N = get_nested(report, ["data", "N"])
        invalid_count = get_nested(report, ["data", "invalid_count"])
        if isinstance(N, int) and isinstance(invalid_count, int) and invalid_count > N:
            extra_errors.append(f"data.invalid_count ({invalid_count}) > data.N ({N})")

        # CI arrays order checks
        # We scan known locations
        ci_paths = [
            ("metrics.rank.ci95", get_nested(report, ["metrics", "rank", "ci95"])),
            ("metrics.subspace.ci95", get_nested(report, ["metrics", "subspace", "ci95"])),
            ("metrics.branching.ci95", get_nested(report, ["metrics", "branching", "ci95"])),
        ]
        baseline_ci = get_nested(report, ["baseline", "distance_ci95"])
        if baseline_ci is not None:
            ci_paths.append(("baseline.distance_ci95", baseline_ci))

        for label, ci in ci_paths:
            if isinstance(ci, list) and len(ci) == 2 and all(isinstance(x, (int, float)) for x in ci):
                msg = ensure_ci_order([float(ci[0]), float(ci[1])], label)
                if msg:
                    extra_errors.append(msg)

        # Value inside CI checks (tolerant)
        check_required_numeric_in_ci("metrics.rank.rho", get_nested(report, ["metrics", "rank", "rho"]), get_nested(report, ["metrics", "rank", "ci95"]), extra_errors)
        check_required_numeric_in_ci("metrics.subspace.rho", get_nested(report, ["metrics", "subspace", "rho"]), get_nested(report, ["metrics", "subspace", "ci95"]), extra_errors)
        check_required_numeric_in_ci("metrics.branching.H", get_nested(report, ["metrics", "branching", "H"]), get_nested(report, ["metrics", "branching", "ci95"]), extra_errors)

        # Baseline invariants
        baseline = report.get("baseline")
        if isinstance(baseline, dict):
            # distance inside CI
            check_required_numeric_in_ci("baseline.distance", baseline.get("distance"), baseline.get("distance_ci95"), extra_errors)

            # thresholds monotonic
            thr = baseline.get("thresholds")
            if isinstance(thr, dict):
                g, y, r = thr.get("green"), thr.get("yellow"), thr.get("red")
                if all(isinstance(v, (int, float)) for v in [g, y, r]):
                    if not (float(g) <= float(y) + TOL and float(y) <= float(r) + TOL):
                        extra_errors.append(f"baseline.thresholds must satisfy green<=yellow<=red, got {thr}")
                else:
                    extra_errors.append("baseline.thresholds must contain numeric green/yellow/red")

            # forbidden classification
            cls = baseline.get("classification")
            if isinstance(cls, str) and cls in forbid:
                extra_errors.append(f"Forbidden baseline.classification='{cls}'")

            # optional consistency between distance and thresholds
            if strict_classification and isinstance(thr, dict) and all(isinstance(thr.get(k), (int, float)) for k in ["green", "yellow", "red"]) and isinstance(baseline.get("distance"), (int, float)) and isinstance(cls, str):
                dist = float(baseline["distance"])
                green = float(thr["green"])
                yellow = float(thr["yellow"])
                red = float(thr["red"])
                if cls == "Within Baseline Envelope" and dist > yellow + TOL:
                    extra_errors.append(f"classification='{cls}' but distance={dist} > yellow={yellow}")
                if cls == "Strong Deviation" and dist < red - TOL:
                    extra_errors.append(f"classification='{cls}' but distance={dist} < red={red}")
                if cls == "Deviating" and not (green - TOL <= dist <= red + TOL):
                    extra_errors.append(f"classification='{cls}' but distance={dist} not in [green, red]")

        # Standard diagnostic disclaimer check
        if not has_required_disclaimer(report.get("notes")):
            disclaimer_msg = f"notes missing standard disclaimer: '{DISCLAIMER_TEXT}'"
            if require_disclaimer:
                extra_errors.append(disclaimer_msg)
            else:
                extra_warnings.append(disclaimer_msg)

        # Emit
        if extra_errors:
            any_failed = True
            print(f"::group::Extra invariant errors in {f}")
            for msg in extra_errors:
                gh_error(f, msg)
            print("::endgroup::")

            write_summary_line(f"## ❌ `{f}`")
            for msg in extra_errors[:25]:
                write_summary_line(f"- {msg}")
            if len(extra_errors) > 25:
                write_summary_line(f"- …and {len(extra_errors) - 25} more")
            write_summary_line("")
            continue

        # If there are warnings, show them but do not fail
        if extra_warnings:
            print(f"::group::Extra invariant warnings in {f}")
            for msg in extra_warnings:
                gh_warning(f, msg)
            print("::endgroup::")

        print(f"✅ {f}: OK (schema + invariants)")
        write_summary_line(f"## ✅ `{f}`")
        write_summary_line("- Schema OK")
        write_summary_line("- Extra invariants OK")
        write_summary_line("")
    return 1 if any_failed else 0
