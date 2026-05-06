"""Alert rule registry.

Rules are seeded from ``deploy/alert_rules.yaml`` at startup and kept in an
in-memory dict that can be mutated via the admin API.  The file path is
relative to the repository root so both ``uvicorn`` (run from ``backend/``)
and tests (run from repo root) can locate it.
"""

from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Callable, Mapping

import yaml

from app.models.alert import AlertOperator, AlertRule, AlertRuleCreate, AlertSeverity

_lock = threading.Lock()
_rules: dict[str, AlertRule] = {}

# Candidate paths for the bundled YAML, searched in order.
_YAML_CANDIDATES = [
    Path(__file__).parent.parent.parent.parent / "deploy" / "alert_rules.yaml",
    Path("deploy/alert_rules.yaml"),
]

# ------------------------------ helpers ------------------------------------

_OP_FN: dict[AlertOperator, Callable[[float, float], bool]] = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}


def eval_rule(rule: AlertRule, value: float) -> bool:
    """Return True if *value* satisfies the rule's threshold condition."""
    fn = _OP_FN.get(rule.operator)
    return fn(value, rule.threshold) if fn else False


# ------------------------------ loading ------------------------------------

def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_rules_from_yaml(path: Path | None = None) -> None:
    """Load (or reload) alert rules from a YAML file.

    Called automatically during app startup; can also be called in tests to
    reset to a known state.
    """
    yaml_path = path
    if yaml_path is None:
        for candidate in _YAML_CANDIDATES:
            if candidate.exists():
                yaml_path = candidate
                break

    if yaml_path is None or not yaml_path.exists():
        return

    with yaml_path.open() as fh:
        data: Mapping = yaml.safe_load(fh) or {}

    raw_rules: list[dict] = data.get("rules", [])
    with _lock:
        for entry in raw_rules:
            rule = AlertRule(
                id=entry.get("id") or _slug(entry["name"]),
                name=entry["name"],
                metric=entry["metric"],
                operator=entry.get("operator", ">"),
                threshold=float(entry["threshold"]),
                severity=AlertSeverity(entry.get("severity", "medium")),
                source=entry.get("source", "system"),
                enabled=entry.get("enabled", True),
            )
            _rules[rule.id] = rule


# ------------------------------ CRUD ----------------------------------------

def list_rules() -> list[AlertRule]:
    with _lock:
        return list(_rules.values())


def get_rule(rule_id: str) -> AlertRule | None:
    with _lock:
        return _rules.get(rule_id)


def upsert_rule(rule_id: str, payload: AlertRuleCreate) -> AlertRule:
    rule = AlertRule(id=rule_id, **payload.model_dump())
    with _lock:
        _rules[rule_id] = rule
    return rule


def delete_rule(rule_id: str) -> bool:
    with _lock:
        return _rules.pop(rule_id, None) is not None


def rules_for_metric(metric: str) -> list[AlertRule]:
    with _lock:
        return [r for r in _rules.values() if r.metric == metric and r.enabled]


# Seed defaults on import so the service is immediately usable.
load_rules_from_yaml()
