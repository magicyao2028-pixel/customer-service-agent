from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from .evaluation import evaluate_cases
from .feedback import replay_feedback
from .privacy_evaluation import evaluate_redaction_cases


COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")


def load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def validate_evidence_index(root: Path, payload: dict[str, Any]) -> list[dict[str, Any]]:
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Evidence index must contain claims")
    root = root.resolve()
    seen: set[str] = set()
    checked = []
    for claim in claims:
        if not isinstance(claim, dict) or not str(claim.get("claim_id", "")).strip() or not str(claim.get("statement", "")).strip():
            raise ValueError("Every evidence claim needs claim_id and statement")
        claim_id = claim["claim_id"]
        if claim_id in seen:
            raise ValueError(f"Duplicate evidence claim_id: {claim_id}")
        seen.add(claim_id)
        artifacts = claim.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError(f"{claim_id} must link artifacts")
        paths = []
        for artifact in artifacts:
            relative = str(artifact.get("path", "")) if isinstance(artifact, dict) else ""
            target = (root / relative).resolve()
            if not isinstance(artifact, dict) or not str(artifact.get("kind", "")).strip() or not relative or not target.is_relative_to(root) or not target.is_file():
                raise ValueError(f"Missing, unsafe or untyped evidence path: {relative}")
            paths.append(relative)
        checked.append({"claim_id": claim_id, "artifact_paths": paths, "passed": True})
    return checked


def validate_external_intake(payload: dict[str, Any]) -> list[dict[str, Any]]:
    date.fromisoformat(str(payload.get("reviewed_on", "")))
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("External intake must contain candidates")
    checks = []
    for item in candidates:
        required = {"repository", "version", "commit", "license", "decision", "code_adopted", "reason"}
        if not isinstance(item, dict) or required.difference(item):
            raise ValueError("External candidate metadata is incomplete")
        if not str(item["repository"]).startswith("https://github.com/") or not COMMIT_PATTERN.fullmatch(str(item["commit"])):
            raise ValueError("External repository or full commit SHA is invalid")
        if item["decision"] not in {"adopted", "rejected"} or not isinstance(item["code_adopted"], bool) or (item["decision"] == "adopted") != item["code_adopted"]:
            raise ValueError("External decision is invalid or inconsistent")
        checks.append({"repository": item["repository"], "decision": item["decision"], "passed": True})
    return checks


def validate_feedback(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    required = {"feedback_id", "source_type", "recorded_on", "classification", "decision", "summary", "acceptance_test", "implementation", "release_result"}
    if required.difference(payload) or any(not str(payload[key]).strip() for key in required):
        raise ValueError("Feedback record is incomplete")
    date.fromisoformat(str(payload["recorded_on"]))
    if payload["source_type"] not in {"real", "synthetic"} or payload["classification"] not in {"defect", "requirement", "usability", "performance", "safety", "documentation"}:
        raise ValueError("Feedback source_type or classification is unsupported")
    if payload["decision"] != "accepted":
        raise ValueError("Trial feedback case must be accepted")
    for key in ("acceptance_test", "implementation"):
        target = (root.resolve() / str(payload[key])).resolve()
        if not target.is_relative_to(root.resolve()) or not target.is_file():
            raise ValueError(f"Feedback {key} path is missing or unsafe")
    return {"feedback_id": payload["feedback_id"], "source_type": payload["source_type"], "passed": True}


def run_trial(root: Path) -> dict[str, Any]:
    root = root.resolve()
    privacy = evaluate_redaction_cases(root / "data/redaction_quality_cases.json")
    behavior = evaluate_cases(root / "data/support_policies.json", root / "data/evaluation_cases.json")
    feedback_replay = replay_feedback(root / "data/support_policies.json", root / "data/reviewer_feedback.json")
    evidence = validate_evidence_index(root, load_json_object(root / "evidence/evidence_index.json"))
    external = validate_external_intake(load_json_object(root / "evidence/external_intake.json"))
    feedback = validate_feedback(root, load_json_object(root / "evidence/feedback_case.json"))
    core_passed = privacy["summary"]["failed"] == 0 and behavior["summary"]["passed_cases"] == 5 and feedback_replay["summary"]["passed"] == 2
    return {
        "schema_version": "1.0", "trial_id": "TRIAL-SERVICE-001", "source_data": "synthetic",
        "overall_passed": core_passed and feedback["passed"] and all(item["passed"] for item in evidence + external),
        "core_flow": {"passed": core_passed, "redaction_cases": privacy["summary"], "behavior_cases_passed": behavior["summary"]["passed_cases"], "feedback_replay_passed": feedback_replay["summary"]["passed"], "external_actions_executed": 0},
        "feedback_regression": feedback, "external_intake": external, "evidence_index": evidence,
        "boundaries": load_json_object(root / "evidence/evidence_index.json")["boundaries"],
    }


def write_trial_report(root: Path, json_path: Path, markdown_path: Path) -> dict[str, Any]:
    report = run_trial(root)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text("\n".join([
        "# Customer Service Trial Readiness", "", "> Synthetic offline verification; no ticketing write or customer reply is executed.", "",
        f"- Overall: **{'PASS' if report['overall_passed'] else 'FAIL'}**",
        f"- Redaction cases: {report['core_flow']['redaction_cases']['passed']}/{report['core_flow']['redaction_cases']['total']}",
        f"- Behavior cases: {report['core_flow']['behavior_cases_passed']}/5",
        f"- Feedback replay: {report['core_flow']['feedback_replay_passed']}/2", "", "## Pilot boundary", "",
        *[f"- {item}" for item in report["boundaries"]], "",
    ]), encoding="utf-8")
    return report
