import json
from pathlib import Path

import pytest

from ond_art_ci_pack import validator

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "ond-art-report-0.1.schema.json"


def base_report() -> dict:
    return {
        "spec": {
            "name": "OND-ART",
            "version": "0.1",
            "profile": "core",
        },
        "run": {
            "run_id": "2026-02-03T12:00:00+00:00#test",
            "created_at": "2026-02-03T12:00:00+00:00",
            "timezone": "America/New_York",
        },
        "context": {
            "protocol": "signature",
            "scheme": "ECDSA-P256",
            "params": {
                "hash": "SHA-256",
            },
            "public_context_hash": "sha256:deadbeef",
        },
        "data": {
            "N": 10000,
            "order": "generation_index",
            "message_policy": "fixed-set-v1",
            "invalid_count": 0,
        },
        "pi": {
            "pi_id": "ecdsa-ur-uz-v1",
            "pi_version": "1.0.0",
            "pi_spec_hash": "sha256:cafebabe",
            "obs_space": {
                "type": "R^d",
                "d": 2,
            },
        },
        "bootstrap": {
            "B": 200,
            "method": "percentile",
            "unit": "U",
            "block_length": 0,
        },
        "metrics": {
            "rank": {
                "H": 0.65,
                "rho": 0.94,
                "ci95": [0.92, 0.95],
                "svd_settings": {"eps": 1e-12},
            },
            "subspace": {
                "H": 5.1,
                "rho": 0.71,
                "ci95": [0.68, 0.74],
                "binning": {"b": 8, "M_occ": 512},
            },
            "branching": {
                "H": 1.85,
                "ci95": [1.78, 1.92],
                "clustering": {"method": "kmeans", "K": 316, "seed": 0},
            },
        },
        "baseline": None,
        "notes": ["Diagnostic only; no security claim."],
    }


def run_validator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reports: list[dict], env: dict | None = None) -> int:
    for idx, report in enumerate(reports):
        (tmp_path / f"report-{idx}.json").write_text(json.dumps(report), encoding="utf-8")

    monkeypatch.setenv("SCHEMA_PATH", str(SCHEMA_PATH))
    monkeypatch.setenv("REPORT_GLOB", str(tmp_path / "*.json"))
    if env:
        for key, value in env.items():
            monkeypatch.setenv(key, value)
    return validator.main()


def test_invalid_count_exceeds_n_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = base_report()
    report["data"]["N"] = 10
    report["data"]["invalid_count"] = 11
    exit_code = run_validator(tmp_path, monkeypatch, [report])
    assert exit_code == 1


def test_ci_order_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = base_report()
    report["metrics"]["rank"]["ci95"] = [0.95, 0.92]
    exit_code = run_validator(tmp_path, monkeypatch, [report])
    assert exit_code == 1


def test_require_disclaimer_fails_when_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = base_report()
    report["notes"] = ["No disclaimer here"]
    exit_code = run_validator(tmp_path, monkeypatch, [report], env={"REQUIRE_DISCLAIMER": "1"})
    assert exit_code == 1


def test_strict_classification_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = base_report()
    report["baseline"] = {
        "baseline_id": "release-1",
        "distance": 0.3,
        "distance_ci95": [0.28, 0.31],
        "classification": "Within Baseline Envelope",
        "thresholds": {"green": 0.1, "yellow": 0.2, "red": 0.4},
    }
    exit_code = run_validator(tmp_path, monkeypatch, [report], env={"STRICT_CLASSIFICATION": "1"})
    assert exit_code == 1


def test_schema_requires_params_hash_for_ecdsa_p256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = base_report()
    report["context"]["params"] = {}
    exit_code = run_validator(tmp_path, monkeypatch, [report])
    assert exit_code == 1


def test_obs_space_requires_d_for_r_d(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report = base_report()
    report["pi"]["obs_space"] = {"type": "R^d"}
    exit_code = run_validator(tmp_path, monkeypatch, [report])
    assert exit_code == 1
